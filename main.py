from __future__ import print_function

import asyncio
import pickle
import os.path
from datetime import datetime, timedelta
from time import sleep
from typing import List, Tuple, Iterable
from hashlib import sha1

from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from requests.exceptions import ConnectionError
from aiohttp import BasicAuth
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, PROXY_HOST, PROXY_PASS, PROXY_PORT, PROXY_USERNAME, DESTINATION_CHANNEL
from models import Row, TableCheck
from config import SAMPLE_SPREADSHEET_ID

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# SAMPLE_RANGE_NAME = 'Class Data!A2:E'

try:
    PROXY_AUTH = None
    PROXY_URL = None
    response = requests.get('https://api.telegram.org')
except ConnectionError as e:
    PROXY_URL = f"socks5://{PROXY_HOST}:{PROXY_PORT}"
    PROXY_AUTH = BasicAuth(login=PROXY_USERNAME, password=PROXY_PASS)
bot = Bot(token=BOT_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
dp = Dispatcher(bot)


def get_credentials():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return credentials


def init_db():
    Row.create_table(fail_silently=True)
    TableCheck.create_table(fail_silently=True)


def calc_hash(row: List[str]) -> str:
    string_row_representation = ''.join(row)
    hash_factory = sha1()
    hash_factory.update(string_row_representation.encode('utf-8'))

    return hash_factory.hexdigest()


def last_n_table_checks(n: int = 5) -> Iterable:
    return TableCheck.select().order_by(TableCheck.check_dt.desc()).limit(n)


def is_table_stable():
    table_checks = last_n_table_checks()
    hashes = [item.table_hash for item in table_checks]

    if len(set(hashes)) > 1:
        return False

    return True


def clear_obsolete_entries() -> int:
    now = datetime.now()
    time_ago = now - timedelta(minutes=10)
    query = TableCheck.delete().where(TableCheck.check_dt < time_ago)

    return query.execute()


def get_header_and_table(service: Resource) -> Tuple[list, List]:
    sheet: Resource = service.spreadsheets()
    response = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="A1:I").execute()

    table = response['values']
    header = table[0]
    del table[0]

    return header, table


def save_table_state(table: List[List[str]]):
    string_rows = [''.join(row) for row in table]

    table_hash = calc_hash(string_rows)

    TableCheck.create(check_dt=datetime.now(),
                      table_hash=table_hash)


def run_loop(service: Resource) -> None:
    interval = 3
    while True:
        sleep(interval)

        header, table = get_header_and_table(service)

        clear_obsolete_entries()
        save_table_state(table)

        if not is_table_stable():
            continue

        for i, row in enumerate(table):
            row_hash = calc_hash(row)

            try:
                saved_row, created = Row.get_or_create(index=i,
                                                       creation_dt=row[0],
                                                       salon=row[1],
                                                       manager=row[2],
                                                       new_clients=row[3],
                                                       new_calculation=row[4],
                                                       repeated_calculation=row[5],
                                                       distributed_cutaways=row[6],
                                                       sales=row[7],
                                                       revenue=row[8],
                                                       row_hash=row_hash)
            except:
                continue

            if created:
                message_text = f"Время: *{row[0]}*\n" \
                    f"Наименование салона: *{row[1]}*\n" \
                    f"Менеджер: *{row[2]}*\n" \
                    f"Количество новых клиентов: *{row[3]}*\n" \
                    f"Количество новых просчётов: *{row[4]}*\n" \
                    f"Количество повторных просчётов: *{row[5]}*\n" \
                    f"Количество розданных визиток: *{row[6]}*\n" \
                    f"Количество продаж: *{row[7]}*\n" \
                    f"Выручка: *{row[8]}*"
                loop = asyncio.get_event_loop()
                loop.run_until_complete(bot.send_message(DESTINATION_CHANNEL, message_text, parse_mode='Markdown'))


def main():
    init_db()

    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    run_loop(service)


if __name__ == '__main__':
    main()
