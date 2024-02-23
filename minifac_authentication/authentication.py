

import os
import datetime
from threading import Lock
from functools import wraps

from flask import Flask, request, make_response
import mysql.connector

import jwt
from jwt.exceptions import InvalidSignatureError


with open('/run/secrets/accounts_auth', 'r') as rfl:
    JWT_ALGORITHM, JWT_SECRET = rfl.read().split()


class MySQL_Connection():
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST')
        self.port = os.getenv('MYSQL_PORT')
        self.dbname = os.getenv('MYSQL_DBNAME')
        with open('/run/secrets/mysql_auth', 'r') as rfl:
            self.user, self.pswd = rfl.read().split()
        self.lock = Lock()

    def __enter__(self):
        self.lock.acquire()
        self._conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            passwd=self.pswd,
            database=self.dbname,
        )
        return self._conn

    def __exit__(self, *args):
        self._conn.close()
        self.lock.release()


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return {
        'status': 'success',
        'message': 'welcome to authentication api'
    }, 200


@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization

    if (auth is None) or (auth.username is None) or (auth.password is None):
        return {
            'status': 'fail',
            'message': 'invalid authorization attribute'
        }, 400

    try:
        with mysql_connect as conn:
            with conn.cursor() as curs:
                # check database connection
                curs.execute(
                    f'''
                    SELECT username, password
                    FROM minifac_db.accounts
                    WHERE username = '{auth.username}'
                    ;''')
                resp = curs.fetchone()
    except Exception:
        return {
            'status': 'fail',
            'message': 'bad database connection'
        }, 500

    if resp:
        db_username, db_password = resp
    else:
        return {
            'status': 'fail',
            'message': 'invalid username or password'
        }, 401

    if (db_username == auth.username) and (db_password == auth.password):
        iat = datetime.datetime.utcnow()
        exp = iat + datetime.timedelta(hours=12)
        resp = make_response(
            {
                'status': 'success',
                'message': 'user login successfully'
            }, 200
        )
        resp.set_cookie(
            'token',
            jwt.encode(
                {
                    'sub': auth.username,
                    'exp': exp.timestamp()
                },
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            ),
            httponly=True
        )
        return resp
    else:
        return {
            'status': 'fail',
            'message': 'invalid username or password'
        }, 401


def with_validation(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not (token := request.cookies.get('token')):
            return {
                'status': 'fail',
                'message': 'token not found'
            }, 401
        try:
            claims = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=JWT_ALGORITHM
            )
        except InvalidSignatureError:
            return {
                'status': 'fail',
                'message': 'invalid token'
            }, 401

        if datetime.datetime.utcnow().timestamp() <= claims['exp']:
            return func(claims)
        else:
            return {
                'status': 'fail',
                'message': 'token expired'
            }, 401
    return decorated_function


@app.route('/validate', methods=['GET'])
@with_validation
def validate(claims):
    return {
        'status': 'success',
        'message': f'token valid: {claims}'
    }, 200
