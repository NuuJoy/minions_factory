

from typing import Tuple, Any
import os
import time
import json

from flask import Flask, request
import requests

from minifac_utils import MySQL_Connection, with_validation


with open('/run/secrets/accounts_auth', 'r') as rfl:
    for name in ('JWT_ALGORITHM', 'JWT_SECRET'):
        os.environ[name] = rfl.readline().strip()


with open('process_endpoints.txt', 'r') as rfl:
    PROCESS_ENDPOINTS = rfl.read().split()


def publish_message(message: Any) -> None:
    print(f'publishing message: {message}')
    for endpoint in PROCESS_ENDPOINTS:
        print(f'to {endpoint}')
        requests.post(url=endpoint, json=message)
    print('publishing message done')


mysql_connect = MySQL_Connection()


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    print('index')
    return {
        'status': 'success',
        'message': 'welcome to workloader api'
    }, 200


@app.route('/add_workorders', methods=['POST'])
@with_validation
def add_workorders(claims):
    start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    username = claims['sub']
    orders = request.json['orders']
    with mysql_connect as conn:
        with conn.cursor() as curs:
            try:
                for (head_id, body_id, arms_id, legs_id) in orders:
                    print('add_workorders: create workorder')
                    curs.execute(
                        f'''
                        INSERT
                            minifac_db.workorder (
                                username,
                                HeadPartID, BodyPartID, ArmsPartID, LegsPartID,
                                Status
                            )
                        VALUES
                            (
                                "{username}",
                                {head_id}, {body_id}, {arms_id}, {legs_id},
                                "Create"
                            )
                        ;'''
                    )
                    print('add_workorders: get order_id')
                    curs.execute(
                        '''
                        SELECT OrderID
                        FROM minifac_db.workorder
                        WHERE Status = "Create"
                        ;'''
                    )
                    order_id = curs.fetchall()[-1][0]
                    print('add_workorders: create workprocess')
                    curs.execute(
                        f'''
                        INSERT
                            minifac_db.workprocess (
                                OrderID, Process, Status, StartTime
                            )
                        VALUES
                            (
                                {order_id}, "Create", "Success", "{start_time}"
                            )
                        ;'''
                    )
                    publish_message([order_id, 'Create', 'Success'])

                print('add_workorders: commit')
                conn.commit()

                return {
                    'status': 'success',
                    'message': 'add workorders successfully',
                }, 200
            except Exception:
                return {
                    'status': 'fail',
                    'message': 'add workorders failed',
                }, 401


@app.route('/process_report', methods=['POST'])
def process_report() -> tuple[dict[str, str], int]:
    message: Tuple[str, str, str, str] = request.json['message']
    order_id, process, status, start_time = message
    with mysql_connect as conn:
        with conn.cursor() as curs:
            curs.execute(
                f'''
                INSERT
                    minifac_db.workprocess (
                        OrderID, Process, Status, StartTime
                    )
                VALUES
                    ({order_id}, "{process}", "{status}", "{start_time}")
                ;'''
            )
            curs.execute(
                f'''
                UPDATE
                    minifac_db.workorder
                SET
                    Status = "{process}"
                WHERE
                    OrderID = {order_id}
                ;'''
            )
            conn.commit()
    publish_message([order_id, process, status])
    return {
        'status': 'success',
        'message': 'report successfully',
    }, 200
