import os

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters
from telegram import Document
import nltk
import logging
import mysql.connector
from mysql.connector import MySQLConnection, Error, errorcode, connect
from pathlib import Path

from bookparser import BookSplitter

BOOKS_DIR = "downloaded_books"
NO_RIGHTS_MSG = "У вас нет прав на использование этого бота"
GREET_MSG = "Добро пожаловать в бот-админку"

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'database': 'book_divination'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def check_for_admin(chat_id: int) -> bool:
    # TODO: check userId in db
    # return bool
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if check_for_admin(chat_id):
        await context.bot.send_message(chat_id, text=GREET_MSG)
    else:
        await context.bot.send_message(chat_id, text=NO_RIGHTS_MSG)

def insert_book_into_db(file_path: str):
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            parser = BookSplitter()
            parser.read_book(file_path)
            parser.insert_into_db(connection)
            logging.info('insert_book_into_db complete!')
    except Error as err:
        logging.error(err)

async def new_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not check_for_admin(chat_id):
        # return
        context.bot.send_message(chat_id, text=NO_RIGHTS_MSG)
    # getting file and saving it to directory
    await context.bot.send_message(chat_id, text='Файл получен. Обработка...')
    # try:
    attachment = update.effective_message.effective_attachment
    print(attachment)
    print(attachment.file_name)
    new_file = await attachment.get_file()
    path = Path(BOOKS_DIR, attachment.file_name)
    print(path)
    await new_file.download_to_drive(path)
    insert_book_into_db(path)
    logging.info('new_book handler complete!')
    # except Exception as exc:
    #     await context.bot.send_message(chat_id, text=f'Ошибка обработки: {exc}')
    #     raise exc
    # else:
    #     await context.bot.send_message(chat_id, text=f'Файл загружен в базу данных')


def main():
    applaction = ApplicationBuilder().token(os.environ.get('TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    upload_book_handler = MessageHandler(filters.Document.FileExtension('txt'), new_book)
    
    applaction.add_handler(start_handler)
    applaction.add_handler(upload_book_handler)
    applaction.run_polling()

if __name__ == '__main__':
    main()