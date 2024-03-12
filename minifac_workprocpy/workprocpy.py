

from typing import Any, List, Dict, BinaryIO, NoReturn

import os
import time
from dataclasses import dataclass, InitVar
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
from threading import Thread, Lock

import requests


PROCESS_NAME = os.getenv('PROCESS_NAME')
PROCESS_TIME = os.getenv('PROCESS_TIME')
PROCESS_YIELD = os.getenv('PROCESS_YIELD')
PROCESS_REWORK = os.getenv('PROCESS_REWORK')
PROCESS_SCRAP = os.getenv('PROCESS_SCRAP')
PROCESS_CONDS = os.getenv('PROCESS_CONDS')


@dataclass
class Request():
    path: str
    method: str
    headers: Dict[str, str]
    rfile: InitVar[BinaryIO]
    body: str | Dict[str, str] | List[str] = ''

    def __post_init__(self, rfile: BinaryIO) -> None:
        if 'Content-Length' in self.headers:
            length = int(self.headers['Content-Length'])
            self.body = rfile.read(length).decode()
            print('self.body:', type(self.body), self.body)
            try:
                if self.headers['Content-Type'] == 'application/json':
                    print('self.body:', type(self.body), self.body)
                    self.body = json.loads(self.body)
                    print('self.body:', type(self.body), self.body)
            except (KeyError, json.decoder.JSONDecodeError) as err:
                print(err)
                pass


class TaskList():
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasklist: List[str] = []

    def is_task(self) -> bool:
        with self._lock:
            return bool(len(self._tasklist))

    def get_task(self) -> str | None:
        with self._lock:
            if len(self._tasklist):
                return self._tasklist.pop(0)
            else:
                return None

    def add_task(self, task: str) -> None:
        with self._lock:
            self._tasklist.append(task)


class EchoServerRequestHandler(BaseHTTPRequestHandler):
    tasklist: TaskList = TaskList()

    @classmethod
    def add_task(cls, task: str) -> None:
        cls.tasklist.add_task(task)

    def __getattribute__(self, __name: str) -> Any:
        '''response any request-methods with do_ANYMETHODS'''
        if __name.startswith('do_'):
            __name = 'do_ANYMETHODS'
        return super().__getattribute__(__name)

    def get_request(self) -> Request:
        return Request(
            self.path,
            self.command,
            dict(self.headers),
            self.rfile
        )

    def send_resp(self, message: bytes = b'', code: int = 200) -> None:
        super().send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message)

    def do_ANYMETHODS(self) -> None:
        print('enter do_ANYMETHODS')
        assert PROCESS_CONDS is not None, 'PROCESS_CONDS can\'t be None'
        proc_conditions: List[List[str | None]] = json.loads(PROCESS_CONDS)
        request: Request = self.get_request()
        print(request)
        if (request.path == '/inbox') and (request.method == 'POST'):
            print(request.body)
            print(type(request.body))
            order_id, last_station, last_status = request.body

            for station, status in proc_conditions:
                if all((
                    (last_station == station) or (station is None),
                    (last_status == status) or (status is None),
                )):
                    self.add_task(order_id)
                    break
            self.send_resp(json.dumps({
                'status': 'success',
                'message': 'add workorders successfully'
            }).encode())


def run_work_thread(tasklist: TaskList) -> NoReturn:
    assert PROCESS_NAME is not None, 'PROCESS_NAME can\'t be None'
    assert PROCESS_TIME is not None, 'PROCESS_TIME can\'t be None'
    assert PROCESS_YIELD is not None, 'PROCESS_YIELD can\'t be None'
    assert PROCESS_REWORK is not None, 'PROCESS_REWORK can\'t be None'
    assert PROCESS_SCRAP is not None, 'PROCESS_SCRAP can\'t be None'

    proc_time_s = float(PROCESS_TIME)
    proc_yiled = int(PROCESS_YIELD)
    proc_rework = int(PROCESS_REWORK)
    proc_scrap = int(PROCESS_SCRAP)

    while True:
        if order_id := tasklist.get_task():
            print(f'thread got order_id: {order_id} start')
            start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

            time.sleep(proc_time_s + (-0.5 + random.random() * proc_time_s))

            result = random.choices(
                population=['Success', 'Rework', 'Scrap'],
                weights=[proc_yiled, proc_rework, proc_scrap],
                k=1
            )[0]

            requests.post(
                url='http://workloader:8000/process_report',
                json={
                    'status': 'success',
                    'message': [
                        order_id,
                        PROCESS_NAME,
                        result,
                        start_time
                    ]
                }
            )
            print(f'thread got order_id: {order_id} done')
        else:
            time.sleep(1.0)


if __name__ == '__main__':

    Thread(
        target=run_work_thread,
        args=[EchoServerRequestHandler.tasklist]
    ).start()

    with HTTPServer(('0.0.0.0', 8000), EchoServerRequestHandler) as server:
        server.serve_forever()
