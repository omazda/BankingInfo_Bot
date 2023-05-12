import logging
import os
import sys

import mysql.connector as MySQLdb

from telegram.ext import Updater
from telethon import TelegramClient, events

from dotenv import load_dotenv

# Идентификатор чата с финансовыми новостями.
FROM_CHATS = -1001601765215

# Загрузка переменных окружения, которые необходимо вынести
# за код, в константы.
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PSWRD = os.getenv('MYSQL_PSWRD')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
USERNAME = os.getenv('USERNAME')

# Открывается файл для записи логов. Данный файл необходим для выявления и
# исправления ошибок в работе программы.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log',
    filemode='a',
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler(stream=sys.stdout)
)

client = TelegramClient(USERNAME, API_ID, API_HASH)

client.start()


@client.on(events.NewMessage(chats=FROM_CHATS))
async def main(event):
    # Подключение к базе данных MySQL,
    # получение списка пользователей бота
    try:
        connection = MySQLdb.Connect(
            host='localhost',
            user=MYSQL_USER,
            passwd=MYSQL_PSWRD,
            db='banking_chat_mysql'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM chart_users;")
        chats = cursor.fetchall()
    except Exception as error:
        logging.error(
            f'Ошибка при создании таблицы. Таблица уже создана?'
            f' Error: {error}'
        )
    # Рассылка сообщений с обучающими материалами по финансовой грамотности
    if chats is not None:
        for chat in chats:
            # updater.effective_chat = chat
            updater.bot.forward_message(
                chat_id=chat[0],
                from_chat_id=FROM_CHATS,
                message_id=event.message.id
            )
    # Закрытие таблицы и базы данных MySql
    if cursor:
        cursor.close()
    if connection:
        connection.close()


def check_token():
    """Проверка наличия необходимого токена."""
    if TELEGRAM_TOKEN is None:
        error_msg = (
            f'Критическая ошибка! Не определена переменная окружения: '
            f'TELEGRAM_TOKEN.'
        )
        logger.critical(error_msg)
    return TELEGRAM_TOKEN


updater = Updater(token=check_token())
client.run_until_disconnected()
