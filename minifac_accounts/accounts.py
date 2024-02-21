

import os
import datetime
from threading import Lock

from flask import Flask, request
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
        'message': 'welcome to accounts api'
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
                    SELECT
                        username, password
                    FROM
                        minifac_db.accounts
                    WHERE
                        username = '{auth.username}'
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
        auth_token = jwt.encode(
            {
                'sub': auth.username,
                'exp': exp.timestamp()
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        return {
            'status': 'success',
            'message': 'user login successfully',
            'auth_token': auth_token}, 200
    else:
        return {
            'status': 'fail',
            'message': 'invalid username or password'
        }, 401


@app.route('/validate', methods=['POST'])
def validate():
    auth = request.authorization

    if (auth is None) or (auth.type != 'bearer') or (auth.token is None):
        return {
            'status': 'fail',
            'message': 'invalid authorization attribute'
        }, 400

    try:
        claims = jwt.decode(
            auth.token,
            JWT_SECRET,
            algorithms=JWT_ALGORITHM
        )
    except InvalidSignatureError:
        return {
            'status': 'fail',
            'message': 'invalid token'
        }, 401

    if datetime.datetime.utcnow().timestamp() <= claims['exp']:
        return {
            'status': 'success',
            'message': f'welcome {claims["sub"]}',
            'claims': claims
        }, 200
    else:
        return {
            'status': 'fail',
            'message': 'token expired'
        }, 401


@app.route('/get_account_info', methods=['GET'])
def get_account_info():
    validation, statuscode = validate()
    if validation['status'] == 'success':
        username = validation['claims']['sub']
        with mysql_connect as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f'''
                    SELECT
                        CustomerName, Credit
                    FROM
                        minifac_db.accounts
                    WHERE
                        username = '{username}'
                    ;''')
                resp = curs.fetchone()
        name, credit = resp
        return {'name': name, 'credit': credit}, 200
    else:
        return validation, statuscode
