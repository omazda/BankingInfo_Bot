from telethon.sync import TelegramClient
from telethon import TelegramClient, events, utils
import requests
import json
import pymorphy2
import re
import numpy as np
import csv
import time
from dotenv import load_dotenv
import os
min_counts_words = 40
morph = pymorphy2.MorphAnalyzer()
reg = re.compile("[^а-яА-Я- ]")
fn = "message_info.csv"
file = open(fn, "w", newline="")
header = [
    "chars",
    "letters",
    "n_words",
    "n_sentences",
    "avg_syl",
    "index_SMOG",
    "count_top_5_in_Slovar_Slov",
    "Fin_literacy_status",
]
writer = csv.writer(file)
writer.writerow(header)
# Загрузка переменных окружения
teg_telegram = os.getenv('USERNAME')
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
#Считывание словаря финансовых терминов
Slovar_Slov = open("Slovar_Slov.txt", "r", encoding="utf-8").readlines()
column = 2
#Считывание id каналов в тг из groups_for_parse_all_messages.txt каждый раз c новой строки
groups_id = [int(x) for x in list(open("groups_for_parse_all_messages.txt", mode="r"))]
functors_pos = {"INTJ", "PRCL", "CONJ", "PREP"}

#Функция постановки слов в инфинитив
def pos(word, morth=pymorphy2.MorphAnalyzer()):
    return morth.parse(word)[0].tag.POS

#Подключение к Telegram клиенту
with TelegramClient(teg_telegram, api_id, api_hash) as client:
    client.connect()
    if not client.is_user_authorized():
        client.start()
    for group_id in groups_id:
        #Проверка является ли канал фин. грам. направленным(Ручной ввод)
        print(
            "Чат/Группа/Канал",
            client.get_entity(group_id).username,
            "является фин. грам. направленности?",
        )
        print("Введите, если да 1, если нет -1")
        Economic_orientation = int(input())
        count_messages = 0
        for message in client.iter_messages(group_id):
            count_words_in_text = dict()
            unique_words = []
            count_top_5_in_Slovar_Slov = 0
            #Прогон слов через морфологического анализатор
            response = requests.post(
                "http://api.plainrussian.ru/api/1.0/ru/measure/",
                data={"text": message.text},
            )
            #Проверка ответа морфологического анализатора
            if response.status_code == 200:
                try:
                    #проверка минимального количества слов(по умолчанию порог 40 слов) 
                    if not response.json()["metrics"]["n_words"] < min_counts_words:
                        #Превеление теста к нужному виду
                        text = (
                            reg.sub("", message.text.replace("\n", " ")).lower().split()
                        )
                        #Счёт уникальных слов и их проверка
                        for word in text:
                            if pos(word) not in functors_pos and len(word) > 3:
                                processed_word = morph.parse(word)[0].normal_form
                                if not processed_word in count_words_in_text:
                                    count_words_in_text[processed_word] = 0
                                    unique_words.append(processed_word)
                                count_words_in_text[processed_word] += 1
                        unique_words = sorted(
                            unique_words, key=lambda x: count_words_in_text[x]
                        )
                        unique_words.reverse()
                        #Определение количества встречаемости слов из топ 5 слов из словаря финансовых терминов
                        if len(unique_words) >= 5:
                            for i in range(5):
                                if unique_words[i] + "\n" in Slovar_Slov:
                                    count_top_5_in_Slovar_Slov += count_words_in_text[
                                        unique_words[i]
                                    ]
                        else:
                            for i in range(len(unique_words)):
                                if unique_words[i] + "\n" in Slovar_Slov:
                                    count_top_5_in_Slovar_Slov += count_words_in_text[
                                        unique_words[i]
                                    ]
                        #Новая запись в файл csv
                        row = [
                            response.json()["metrics"]["chars"],
                            response.json()["metrics"]["letters"],
                            response.json()["metrics"]["n_words"],
                            response.json()["metrics"]["n_sentences"],
                            response.json()["metrics"]["avg_syl"],
                            response.json()["indexes"]["index_SMOG"],
                            count_top_5_in_Slovar_Slov,
                            Economic_orientation,
                        ]
                        writer.writerow(row)
                        column += 1
                        count_messages += 1
                    #Проверка на количество обработанных сообщений, если слов более 500 приступаем к следующему каналу
                    if count_messages == 500:
                        break
                except json.decoder.JSONDecodeError:
                    print("Ошибка обработки JSON")
#Сохраняем файл
file.close()