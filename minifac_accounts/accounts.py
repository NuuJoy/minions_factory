

import os
import datetime
from threading import Lock
from decimal import Decimal
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
        'message': 'welcome to accounts api'
    }, 200


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


@app.route('/info', methods=['GET'])
@with_validation
def info(claims):
    username = claims['sub']
    keymap = {
        'name': 'CustomerName',
        'credit': 'Credit'
    }
    request_cols = []
    try:
        for col in request.args.to_dict()['cols'].split(','):
            if col in keymap:
                request_cols.append(keymap[col])
    except Exception:
        pass
    if not request_cols:
        return {}, 200

    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                f'''
                SELECT {','.join(request_cols)}
                FROM minifac_db.accounts
                WHERE username = '{username}'
                ;''')
            resp = curs.fetchone()
    name, credit = resp
    return {'name': name, 'credit': credit}, 200


def change_to_credit(username, amount):
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                f'''
                SELECT Credit
                FROM minifac_db.accounts
                WHERE username = '{username}'
                ;'''
            )
            credit = Decimal(curs.fetchone()[0])
            if credit >= amount:
                newcredit = credit + amount
                curs.execute(
                    f'''
                    UPDATE minifac_db.accounts
                    SET Credit = {newcredit}
                    WHERE username = '{username}'
                    ;
                    COMMIT;'''
                )
                return {
                    'status': 'success',
                    'message': 'purchase successfully',
                }, 200
            else:
                return {
                    'status': 'fail',
                    'message': 'not enough credit',
                }, 409


@app.route('/charge', methods=['PATCH'])
@with_validation
def charge(claims):
    amount = Decimal(request.args.to_dict()['amount'])
    if amount <= 0:
        return {
            'status': 'fail',
            'message': 'not support negative amount value'
        }, 400
    return change_to_credit(claims['sub'], -amount)


@app.route('/refund', methods=['PATCH'])
@with_validation
def refund(claims):
    amount = Decimal(request.args.to_dict()['amount'])
    if amount <= 0:
        return {
            'status': 'fail',
            'message': 'not support negative amount value'
        }, 400
    return change_to_credit(claims['sub'], amount)
