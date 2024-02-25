

import os
import datetime

from flask import Flask, request, make_response, render_template, redirect

import jwt

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    body, status = with_validation(lambda claims: (claims, 200))()
    if status == 200:
        return f'Welcome {body["sub"]} !!!', status
    else:
        error = body['message']
        return redirect(f'/login?error={error}')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'error' in (args := request.args.to_dict()):
        error = args['error']
    else:
        error = None

    if request.method == 'GET':
        return render_template('login.html', error=error)
    else:
        username = None
        password = None
        try:
            username = request.authorization.username
            password = request.authorization.password
        except Exception:
            try:
                username = request.form['username']
                password = request.form['password']
            except Exception:
                pass

        if (username is None) or (password is None):
            return redirect('/login?error=invalid login method')

        try:
            with mysql_connect as conn:
                with conn.cursor() as curs:
                    # check database connection
                    curs.execute(
                        f'''
                        SELECT username, password
                        FROM minifac_db.accounts
                        WHERE username = '{username}'
                        ;''')
                    resp = curs.fetchone()
        except Exception:
            return redirect('/login?error=bad database connection')

        if resp:
            db_username, db_password = resp
        else:
            return redirect('/login?error=invalid username or password')

        if (db_username == username) and (db_password == password):
            iat = datetime.datetime.utcnow()
            exp = iat + datetime.timedelta(minutes=5)
            resp = make_response(redirect('/'))
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
            return redirect('/login?error=invalid username or password')
