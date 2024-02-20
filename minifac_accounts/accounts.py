

import os

from flask import Flask, make_response
import mysql.connector


class MySQL_Connect():
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST')
        self.port = os.getenv('MYSQL_PORT')
        self.dbname = os.getenv('MYSQL_DBNAME')
        with open('/run/secrets/mysql_auth', 'r') as rfl:
            self.user, self.pswd = rfl.read().split(',')

    def __enter__(self):
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


mysql_connect = MySQL_Connect()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    with mysql_connect as conn:
        with conn.cursor() as curs:
            # check database connection
            curs.execute('''SELECT * FROM minifac_db.accounts;''')
            curs.fetchall()
    response = make_response('Ready!', 200)
    response.mimetype = "text/plain"
    return response
