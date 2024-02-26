

import os

from flask import Flask, request, make_response, render_template, redirect

import requests
from requests.auth import HTTPBasicAuth

from minifac_utils import with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    token_check = with_validation(lambda _: True)()
    if token_check is not True:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            login_resp = requests.post(
                'http://host.docker.internal:5010/login',
                auth=HTTPBasicAuth(username, password)
            )
            if login_resp.status_code != 200:
                error = login_resp.json()['message']
                return render_template('login.html', error=error)
            else:
                token = login_resp.cookies.get('token')
                resp = redirect('/')
                resp.set_cookie('token', token, httponly=True)
                return resp
        else:
            return render_template('login.html')
    else:
        return render_template('customer_purchase_order.html')


@app.route('/get_page_info', methods=['GET'])
def get_page_info():
    page_info = {}
    token = request.cookies.get('token')
    account_resp = requests.get(
        url='http://host.docker.internal:5020/info?cols=name,credit',
        cookies={'token': token}
    )
    page_info.update(account_resp.json())

    store_resp = requests.get(
        url='http://host.docker.internal:5030/allitems',
        cookies={'token': token}
    )
    page_info.update({'allitems': store_resp.json()})
    return page_info, 200
