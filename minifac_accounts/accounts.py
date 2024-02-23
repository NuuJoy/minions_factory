

import os
from decimal import Decimal

from flask import Flask, request

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
        'message': 'welcome to accounts api'
    }, 200


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
