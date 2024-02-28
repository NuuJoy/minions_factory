

import os
import json

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
    print('index')
    token_check = with_validation(lambda _: True)()
    print('token_check:', token_check)
    if token_check is not True:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print('index, post, user:', username, 'pswd:', password)
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
            print('index, get')
            return render_template('login.html')
    else:
        return render_template('customer_purchase_order.html')


@app.route('/logout', methods=['POST'])
def logout():
    print('logout')
    resp = requests.post('http://authentication:8000/logout')
    return 'Logout successfully', resp.status_code, resp.headers.items()


def get_info(token):
    print('get_info')
    account_resp = requests.get(
        url='http://accounts:8000/info',
        cookies={'token': token}
    )
    return account_resp.json()


def get_allitems(token):
    print('get_allitems')
    store_resp = requests.get(
        url='http://store:8000/allitems',
        cookies={'token': token}
    )
    return store_resp.json()


@app.route('/get_page_info', methods=['GET'])
@with_validation
def get_page_info(claims):
    token = request.cookies.get('token')
    page_info = get_info(token)
    page_info['allitems'] = get_allitems(token)
    print('get_page_info, page_info: ', page_info)
    return page_info, 200


def get_orders_summary(allitems, orders):
    print('get_orders_summary, orders: ', orders)

    def get_info_by_id(allitems, id):
        for item in allitems:
            if item[0] == id:
                return item

    purchase_info_text = []
    total_price = 0
    for i, unit in enumerate(orders, start=1):
        purchase_info_text.append(f'Unit {i}')
        for j, id in enumerate(unit, start=1):
            _, part, color, price = get_info_by_id(allitems, id)
            price = int(price)
            purchase_info_text.append(f'---- No.{j}')
            purchase_info_text[-1] += f', Part: {part}'
            purchase_info_text[-1] += f', Color: {color}'
            purchase_info_text[-1] += f', Price: {price}'
            total_price += price
    purchase_info_text.append(f'Total price: {total_price}')
    return purchase_info_text, total_price


@app.route('/review_purchase', methods=['POST'])
@with_validation
def review_purchase(claims):
    token = request.cookies.get('token')
    orders = json.loads(request.form['orders'])
    print('review_purchase, orders: ', orders)
    credit = int(get_info(token)['credit'])
    allitems = get_allitems(token)
    purchase_info_text, total_price = get_orders_summary(allitems, orders)
    enough_credit = (total_price > 0) and (credit >= total_price)
    return render_template(
        'review_purchase.html',
        purchase_info_text=purchase_info_text,
        enough_credit=enough_credit,
        orders=request.form['orders']
    )


@app.route('/make_purchase', methods=['POST'])
def make_purchase():
    print('make_purchase')
    try:
        token = request.cookies.get('token')
        print('make_purchase, token: ', token)
        orders = json.loads(request.form['orders'])
        print('make_purchase, orders: ', orders)

        allitems = get_allitems(token)
        _, total_price = get_orders_summary(allitems, orders)

        resp = requests.patch(
            url='http://accounts:8000/charge',
            json={'amount': total_price},
            cookies={'token': token}
        )
        print('make_purchase, charge: ', resp.json())
    except Exception as err:
        print('exception:', err)
        print('make_purchase, failed')
        return 'Purchase failed', 401

    if resp.status_code == 200:
        try:
            resp = requests.post(
                url='http://workloader:8000/add_workorders',
                json={'orders': orders},
                cookies={'token': token}
            )
            print('make_purchase, add_workorders: ', resp.json())

            if resp.status_code == 200:
                print('make_purchase, success')
                return 'Purchase successfuuly', 200

        except Exception as err:
            print('exception:', err)
            resp = requests.patch(
                url='http://accounts:8000/refund',
                json={'amount': total_price},
                cookies={'token': token}
            )
            print('make_purchase, refund: ', resp.json())

    print('make_purchase, failed')
    return 'Purchase failed', 401
