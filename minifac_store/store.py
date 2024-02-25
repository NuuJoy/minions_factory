

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
        'message': 'welcome to store api'
    }, 200


@app.route('/allitems', methods=['GET'])
@with_validation
def allitems(claims):
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                '''
                SELECT Part, Color, Price
                FROM minifac_db.pricelist
                ;'''
            )
            resp = curs.fetchall()
    return resp, 200
