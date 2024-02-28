

import os

from flask import Flask, request, jsonify

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    print('index')
    return jsonify({
        'status': 'success',
        'message': 'welcome to accounts api'
    }), 200


@app.route('/info', methods=['GET'])
@with_validation
def info(claims):
    username = claims['sub']
    print('info, username:', username)
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                f'''
                SELECT CustomerName, Credit
                FROM minifac_db.accounts
                WHERE username = '{username}'
                ;''')
            resp = curs.fetchone()
    name, credit = resp
    return jsonify({'name': name, 'credit': credit}), 200


def change_to_credit(username, amount):
    print('change_to_credit, username:', username, ', amount:', amount)
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                f'''
                SELECT Credit
                FROM minifac_db.accounts
                WHERE username = '{username}'
                ;'''
            )
            credit = int(curs.fetchone()[0])
            if credit + amount >= 0:
                newcredit = credit + amount
                curs.execute(
                    f'''
                    UPDATE minifac_db.accounts
                    SET Credit = {newcredit}
                    WHERE username = '{username}'
                    ;
                    COMMIT;'''
                )
                return jsonify({
                    'status': 'success',
                    'message': 'purchase successfully',
                }), 200
            else:
                return jsonify({
                    'status': 'fail',
                    'message': 'not enough credit',
                }), 409


@app.route('/charge', methods=['PATCH'])
@with_validation
def charge(claims):
    amount = int(request.json['amount'])
    print('charge, amount:', amount)
    if amount <= 0:
        return jsonify({
            'status': 'fail',
            'message': 'not support negative amount value'
        }), 400
    return change_to_credit(claims['sub'], -amount)


@app.route('/refund', methods=['PATCH'])
@with_validation
def refund(claims):
    amount = int(request.json['amount'])
    print('refund, amount:', amount)
    if amount <= 0:
        return jsonify({
            'status': 'fail',
            'message': 'not support negative amount value'
        }), 400
    return change_to_credit(claims['sub'], amount)
