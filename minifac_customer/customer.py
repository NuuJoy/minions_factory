

import os
import json
from decimal import Decimal

from flask import Flask, request, render_template, redirect

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
                'http://authentication:8000/login',
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
@with_validation
def get_page_info(claims):
    page_info = {}
    token = request.cookies.get('token')
    account_resp = requests.get(
        url='http://accounts:8000/info?cols=name,credit',
        cookies={'token': token}
    )
    page_info.update(account_resp.json())

    store_resp = requests.get(
        url='http://store:8000/allitems',
        cookies={'token': token}
    )
    page_info.update({'allitems': store_resp.json()})
    return page_info, 200


@app.route('/review_purchase', methods=['POST'])
@with_validation
def review_purchase(claims):
    order = json.loads(request.form['order'])
    resp, _ = get_page_info()
    credit = Decimal(resp['credit'])
    allitems = resp['allitems']

    def get_info_by_id(id):
        for item in allitems:
            if item[0] == id:
                return item

    purchase_info_text = []
    total_price = Decimal()
    for i, unit in enumerate(order, start=1):
        purchase_info_text.append(f'Unit {i}')
        for j, id in enumerate(unit, start=1):
            _, part, color, price = get_info_by_id(id)
            price = Decimal(price)
            purchase_info_text.append(f'---- No.{j}')
            purchase_info_text[-1] += f', Part: {part}'
            purchase_info_text[-1] += f', Color: {color}'
            purchase_info_text[-1] += f', Price: {price}'
            total_price += price
    purchase_info_text.append(f'Total price: {total_price}')
    enough_credit = (total_price > 0) and (credit >= total_price)
    return render_template(
        'review_purchase.html',
        purchase_info_text=purchase_info_text,
        enough_credit=enough_credit,
        order=request.form['order']
    )


@app.route('/make_purchase', methods=['POST'])
def make_purchase():
    # communicate with accounts and workloader to make a purchase
    return 'under construction', 200
