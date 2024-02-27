

import os
import datetime
from threading import Lock
from functools import wraps

from flask import request
import mysql.connector

import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError


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
                key=os.environ['JWT_SECRET'],
                algorithms=os.environ['JWT_ALGORITHM']
            )
        except InvalidSignatureError:
            return {
                'status': 'fail',
                'message': 'invalid token'
            }, 401
        except ExpiredSignatureError:
            return {
                'status': 'fail',
                'message': 'token expired'
            }, 401

        return func(claims)
    return decorated_function
