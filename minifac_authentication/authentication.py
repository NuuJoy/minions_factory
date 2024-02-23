

import os
import datetime

from flask import Flask, request, make_response

import jwt

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


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
                key=os.environ['JWT_SECRET'],
                algorithm=os.environ['JWT_ALGORITHM']
            ),
            httponly=True
        )
        return resp
    else:
        return {
            'status': 'fail',
            'message': 'invalid username or password'
        }, 401


@app.route('/validate', methods=['GET'])
@with_validation
def validate(claims):
    return {
        'status': 'success',
        'message': f'token valid: {claims}'
    }, 200
