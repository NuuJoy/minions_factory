

import os
import datetime

from flask import Flask, request, jsonify

import jwt

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    print('index')
    body, status = with_validation(lambda claims: (claims, 200))()
    if status == 200:
        username = body['sub']
        return f'Welcome {username} !!!', status
    else:
        message = body['message']
        return f'Unautherized: {message}'


@app.route('/login', methods=['POST'])
def login():
    username = request.authorization.username
    password = request.authorization.password
    print('login, username:', username, ', password:', password)
    if (username is None) or (password is None):
        return jsonify({
            'status': 'fail', 'message': 'invalid login method'
        }), 400

    try:
        with mysql_connect as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f'''
                    SELECT username, password
                    FROM minifac_db.accounts
                    WHERE username = '{username}'
                    ;''')
                resp = curs.fetchone()
    except Exception:
        return jsonify({
            'status': 'fail', 'message': 'bad database connection'
        }), 503

    if resp:
        db_username, db_password = resp
    else:
        return jsonify({
            'status': 'fail', 'message': 'invalid username or password'
        }), 401

    if (db_username == username) and (db_password == password):
        iat = datetime.datetime.utcnow()
        exp = iat + datetime.timedelta(minutes=5)
        resp = jsonify({
            'status': 'success', 'message': 'login successfully'
        })
        resp.set_cookie(
            'token',
            jwt.encode(
                {
                    'sub': username,
                    'exp': exp.timestamp()
                },
                key=os.environ['JWT_SECRET'],
                algorithm=os.environ['JWT_ALGORITHM']
            ),
            httponly=True
        )
        return resp
    else:
        return jsonify({
            'status': 'fail', 'message': 'invalid username or password'
        }), 401


@app.route('/logout', methods=['POST'])
def logout():
    print('logout')
    resp = jsonify()
    resp.set_cookie('token', httponly=True)
    return resp
