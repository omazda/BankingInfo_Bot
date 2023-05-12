import logging
import os
import sys

import mysql.connector as MySQLdb

from dotenv import load_dotenv

# Загрузка переменных окружения, которые необходимо вынести за код,
# в константы.
load_dotenv()
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PSWRD = os.getenv('MYSQL_PSWRD')

# Открывается файл для записи логов. Данный файл необходим для выявления и
# исправления ошибок в работе программы.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log',
    filemode='w',
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler(stream=sys.stdout)
)

def db_create():
    """Создание базы данных пользователей чата."""
    db_mysql = MySQLdb.connect(
        host='localhost',
        user=MYSQL_USER,
        password=MYSQL_PSWRD
    )
    banking_chat = db_mysql.cursor()
    try:
        banking_chat.execute('CREATE DATABASE banking_chat_mysql')
    except Exception as error:
        logging.error(
            f'Ошибка при создании таблицы. Таблица уже создана?'
            f' Error: {error}'
        )
        banking_chat.execute('USE banking_chat_mysql')
    try:
        banking_chat.execute(
            'create table chart_users '
            '(id BIGINT PRIMARY KEY, '
            'first_name VARCHAR(30), '
            'last_name VARCHAR(30), '
            'username VARCHAR(30))'
        )
    except Exception as error:
        logging.error(
            f'Ошибка при создании столбцов. Столбцы существуют? Error: {error}'
        )
    banking_chat.close()


if __name__ == '__main__':
    db_create()
