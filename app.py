import logging
import os
import sys

import requests
import mysql.connector as MySQLdb
from bs4 import BeautifulSoup
from http import HTTPStatus
from telegram import ReplyKeyboardMarkup
from telegram.ext import Filters, MessageHandler, Updater

from dotenv import load_dotenv
from exceptions import TheAnswerIsNot200Error

# Загрузка переменных окружения, которые необходимо вынести за код,
# в константы.
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PSWRD = os.getenv('MYSQL_PSWRD')

# Константы вынесены за пределы основного кода, для того чтобы в случае
# изменения API Банка России их было легко скорректировать.
ENDPOINT = 'https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'Referer': 'https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx',
    'Content-Type': 'text/xml; charset=utf-8',
    'Content-Length': 'length',
    'SOAPAction': 'http://web.cbr.ru/AllDataInfoXML'
    }
xml = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <AllDataInfoXML xmlns="http://web.cbr.ru/" />
        </soap:Body>
    </soap:Envelope>
    """

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


def handle_message(update, context):
    """Обработка сообщений пользователей."""

    # Импорт констант, определяющих набор фраз для общения с ботом. 
    from vocabulary import (
        START_BOT_MESSAGE,
        RATE_BOT_MESSAGE,
        INFLATION_BOT_MESSAGE,
        USD_BOT_MESSAGE,
        EUR_BOT_MESSAGE,
        GOLD_BOT_MESSAGE,
        SILVER_BOT_MESSAGE,
        PLATINUM_BOT_MESSAGE,
        PALLADIUM_BOT_MESSAGE,
        HELP_BOT_MESSAGE
    )
    # Подключение к базе данных MySQL
    connection = MySQLdb.Connect(
        host='localhost',
        user=MYSQL_USER,
        passwd=MYSQL_PSWRD,
        db='banking_chat_mysql'
    )
    # Получение информации о чате, из которого пришло сообщение.
    chat = update.effective_chat
    # Получение имени владельца чата.
    name = chat.first_name
    # Сохранение ID чата для дальнейшей рассылки
    cursor_object = connection.cursor()
    try:
        cursor_object.execute(
            'insert into chart_users(id, first_name, last_name, username)'
            ' values(%s, %s, %s, %s)',
            (chat.id, chat.first_name, chat.last_name, chat.username)
        )
        connection.commit()
    except Exception as error:
        logging.error(f'Ошибка при записи данных пользователя в БД: {error}')
        connection.rollback()
    connection.close()
    # Запись в переменную finance_info информации о банковских показателях.
    finance_info = get_finance_info()
    # Удаление лишних пробелов и приведение для единообразия к нижнему регистру запроса пользователя.
    telegram_message = update.message.text.lower().replace(
        '   ',
        ' '
    ).replace(
        '  ',
        ' '
    ).strip()

    # Определение набора команд для бота.
    buttons = ReplyKeyboardMarkup(
        [
            ['темпы инфляции', 'ключевая ставка'],
            ['курс доллара', 'курс евро'],
            ['цена золота', 'цена серебра'],
            ['цена платины', 'цена палладия']
        ],
        resize_keyboard=True
    )

    # Обработка запросов пользователя и предоставление ответной информации в зависимости от запроса. 
    if telegram_message in START_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Привет, {name}! Этот финансовый бот'
                f' получает инфу напрямую от Банка России. '
                f'Выбери показатель, значение которого необходимо узнать.'
            ),
            reply_markup=buttons
        )
    elif (
        (update.message.text.lower() in RATE_BOT_MESSAGE) or
        (update.message.text.lower() in INFLATION_BOT_MESSAGE) or
        (update.message.text.lower() in USD_BOT_MESSAGE) or
        (update.message.text.lower() in EUR_BOT_MESSAGE) or
        (update.message.text.lower() in GOLD_BOT_MESSAGE) or
        (update.message.text.lower() in SILVER_BOT_MESSAGE) or
        (update.message.text.lower() in PLATINUM_BOT_MESSAGE) or
        (update.message.text.lower() in PALLADIUM_BOT_MESSAGE)
    ) and ('error' in finance_info):
        print('Error 1')
        context.bot.send_message(
            chat_id=chat.id,
            text=finance_info['error'],
            reply_markup=buttons
        )
    elif telegram_message in HELP_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Привет, {name}! Данный бот сообщает достоверную'
                ' финансовую информацию, обращаясь напрямую к базе '
                ' данных Банка России, а так же присылает банковские новости. '
                'Выбери показатель, значение которого необходимо узнать.'
            ),
            reply_markup=buttons
        )
    elif telegram_message in RATE_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Размер ключевой ставки Банка России установлен с '
                f'{finance_info["key_rate_date"]} в размере '
                f'{finance_info["key_rate_value"]} % годовых.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['key_rate_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in INFLATION_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Годовая инфляция в России по состоянию на '
                f'{finance_info["inflation_date"]} составила '
                f'{finance_info["inflation_value"]} %'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['inflation_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in USD_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Официальный курс доллара США Банком России с '
                f'{finance_info["usd_curs_date"]} установлен в '
                f'размере {finance_info["usd_curs_value"]} руб. за 1 USD.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['usd_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in EUR_BOT_MESSAGE:
        print(telegram_message)
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Официальный курс евро Банком России с '
                f'{finance_info["eur_curs_date"]} установлен в '
                f'размере {finance_info["eur_curs_value"]} руб. за 1 USD.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['eur_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in GOLD_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Учетная цена на золото, установленная Банком России с '
                f'{finance_info["metal_curs_date"]}, равна '
                f'{finance_info["gold_curs_value"]} руб. за 1 г.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['gold_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in SILVER_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Учетная цена на серебро, установленная Банком России с '
                f'{finance_info["metal_curs_date"]}, равна '
                f'{finance_info["silver_curs_value"]} руб. за 1 г.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['silver_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in PLATINUM_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Учетная цена на платину, установленная Банком России с '
                f'{finance_info["metal_curs_date"]}, равна '
                f'{finance_info["platinum_curs_value"]} руб. за 1 г.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['platinum_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    elif telegram_message in PALLADIUM_BOT_MESSAGE:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'Учетная цена на палладий, установленная Банком России с '
                f'{finance_info["metal_curs_date"]}, равна '
                f'{finance_info["palladium_curs_value"]} руб. за 1 г.'
            )+(
                ' Попробуйте отправить запрос позднее.'
                if finance_info['palladium_curs_value'] == '<error: blank data>'
                else ''
            ),
            reply_markup=buttons
        )
    else:
        context.bot.send_message(
            chat_id=chat.id,
            text=(
                'Не удалось распознать команду! '
                'Попробуйте еще раз или выберите команду из меню.'
            ),
            reply_markup=buttons
        )


def get_finance_info():
    """Получает информацию через API Банка России."""

    findata = {}

    # Отправка запросов к серверу и логгирование ошибок.
    try:
        base_response = requests.post(ENDPOINT, data=xml, headers=HEADERS)
        if base_response.status_code == HTTPStatus.OK:
            data = base_response.content
        else:
            error_msg = (
                f'Ошибка! Сервис по адресу {ENDPOINT} недоступен.'
                f' Код ответа API: {base_response.status_code}'
            )
            logger.error(error_msg)
            raise TheAnswerIsNot200Error(error_msg)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        findata['error'] = 'Ошибка получения данных, попробуйте позднее!'
        return findata

    # Считывания информации из ответа сервера с помощью команд библиотеки BeautifulSoup.
    # Проверка наличия необходимой информации в ответах.
    soup = BeautifulSoup(data, features='xml')
    usd_tag = soup.find_all('USD')
    try:
        usd_curs_tag = usd_tag[0].find_all('curs')
    except Exception as error:
        logging.error(f'В ответе сервера отсутствуют данные по "usd": {error}')
        findata['usd_curs_value'] = '<error: blank data>'
        findata['usd_curs_date'] = '<error: blank data>'
    else:
        findata['usd_curs_value'] = usd_curs_tag[0].text
        findata['usd_curs_date'] = usd_tag[0].get('OnDate')
    eur_tag = soup.find_all("EUR")
    try:
        eur_curs_tag = eur_tag[0].find_all('curs')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "eur"'
            f': {error}'
        )
        findata['eur_curs_value'] = '<error: blank data>'
        findata['eur_curs_date'] = '<error: blank data>'
    else:
        findata['eur_curs_value'] = eur_curs_tag[0].text
        findata['eur_curs_date'] = eur_tag[0].get('OnDate')
    gold_tag = soup.find_all('Золото')
    try:
        findata['gold_curs_value'] = gold_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "gold"'
            f': {error}'
        )
        findata['gold_curs_value'] = '<error: blank data>'
    silver_tag = soup.find_all('Серебро')
    try:
        findata['silver_curs_value'] = silver_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "silver"'
            f': {error}'
        )
        findata['silver_curs_value'] = '<error: blank data>'
    platinum_tag = soup.find_all('Платина')
    try:
        findata['platinum_curs_value'] = platinum_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "platinum"'
            f': {error}'
        )
        findata['platinum_curs_value'] = '<error: blank data>'
    palladium_tag = soup.find_all('Палладий')
    try:
        findata['palladium_curs_value'] = palladium_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "palladium"'
            f': {error}'
        )
        findata['palladium_curs_value'] = '<error: blank data>'
    metal_curs = soup.find_all('Metall')
    try:
        findata['metal_curs_date'] = metal_curs[0].get('OnDate')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по дате '
            f'торгов металлами: {error}'
        )
        findata['metal_curs_date'] = '<error: blank data>'
    key_rate_tag = soup.find_all('KEY_RATE')
    try:
        findata['key_rate_value'] = key_rate_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "key_rate_value"'
            f': {error}'
        )
        findata['key_rate_value'] = '<error: blank data>'
    try:
        findata['key_rate_date'] = key_rate_tag[0].get('date')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "key_rate_date"'
            f': {error}'
        )
        findata['key_rate_date'] = '<error: blank data>'
    inflation_tag = soup.find_all('Inflation')
    try:
        findata['inflation_value'] = inflation_tag[0].get('val')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "inflation_value"'
            f': {error}'
        )
        findata['inflation_value'] = '<error: blank data>'
    try:
        findata['inflation_date'] = inflation_tag[0].get('OnDate')
    except Exception as error:
        logging.error(
            f'В ответе сервера отсутствуют данные по "inflation_date"'
            f': {error}'
        )
        findata['inflation_date'] = '<error: blank data>'
    return findata


def check_token():
    """Проверка наличия необходимого токена."""
    if TELEGRAM_TOKEN is None:
        error_msg = (
            f'Критическая ошибка! Не определена переменная окружения: '
            f'TELEGRAM_TOKEN.'
        )
        logger.critical(error_msg)
    return TELEGRAM_TOKEN


def main():
    """Запуск бота"""
    # Создание переменной класса Updater, необходимой для получения и обработки сообшений.
    updater = Updater(token=check_token())
    # Регистрация обработчика текстовых сообщений handle_message.
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
    # Применение метода start_polling() позволяет отправлять регулярные запросы для получения обновлений.
    updater.start_polling()
    # Запуск режима Idle, который будет работать до нажатия Ctrl-C.
    updater.idle()


if __name__ == '__main__':
    main()
