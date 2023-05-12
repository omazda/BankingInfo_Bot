import logging
import os
import sys

from telethon import TelegramClient, events

from dotenv import load_dotenv

# Идентификатор чата с финансовыми новостями (@fincult_info).
CHAT = -1001612316367

# Идентификатор промежуточного чата для пересылки сообщений
# (@ExperimentChannel5)
TARGET_CHAT = -1001601765215

# Загрузка переменных окружения, которые необходимо вынести
# за код, в константы.
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
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


@client.on(events.NewMessage(chats=CHAT))
async def main(event):
    logging.info(
        f'Получено обновление в чате'
        f' {CHAT}'
    )
    await client.forward_messages(TARGET_CHAT, event.message)


client.run_until_disconnected()
