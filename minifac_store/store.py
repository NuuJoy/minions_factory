

import os

from flask import Flask

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    print('index')
    return {
        'status': 'success',
        'message': 'welcome to store api'
    }, 200


@app.route('/allitems', methods=['GET'])
@with_validation
def allitems(claims):
    print('allitems')
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                '''
                SELECT ID, Part, Color, Price
                FROM minifac_db.pricelist
                ;'''
            )
            resp = curs.fetchall()
    return resp, 200
