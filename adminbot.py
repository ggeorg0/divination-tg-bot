import os
from pathlib import Path
import logging

from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, filters
from telegram.ext import CommandHandler, MessageHandler

from bookparse import BookReader
from database import Database

BOOKS_DIR = "downloaded_books"

NO_RIGHTS_MSG = "У вас нет прав на использование этого бота."
GREET_MSG = "Добро пожаловать в бот-админку!"
FILE_UPLOADED_MSG = "Файл получен. Обработка..."
FILE_DONE_MSG = "Файл загружен в базу данных!"
FILE_ERR_MSG = "Неизвестная ошибка обработки файла."
UNICODE_ERR_MSG = "Ошибка кодировки файла! Используйте UTF-8."

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'database': 'book_divination'
}

db: Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if db.check_for_admin(chat_id):
        await context.bot.send_message(chat_id, text=GREET_MSG)
    else:
        await context.bot.send_message(chat_id, text=NO_RIGHTS_MSG)

async def download_file(message: Message) -> Path:
    attachment = message.effective_attachment
    new_file = await attachment.get_file()
    download_path = Path(BOOKS_DIR, attachment.file_name)
    await new_file.download_to_drive(download_path)
    return download_path

async def new_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not db.check_for_admin(chat_id):
        context.bot.send_message(chat_id, text=NO_RIGHTS_MSG)
        return
    await context.bot.send_message(chat_id, text=FILE_UPLOADED_MSG)
    try:
        path = await download_file(update.effective_message)
        db.insert_book(BookReader.read_book(path))
    except UnicodeDecodeError as exc:
        await context.bot.send_message(chat_id, text=UNICODE_ERR_MSG)
        logging.error(exc)
    except Exception as exc:
        await context.bot.send_message(chat_id, text=FILE_ERR_MSG)
        logging.error(exc)
    else:
        await context.bot.send_message(chat_id, text=FILE_DONE_MSG)


def main():
    applaction = ApplicationBuilder().token(os.environ.get('TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    upload_book_handler = MessageHandler(filters.Document.FileExtension('txt'), new_book)
    
    applaction.add_handler(start_handler)
    applaction.add_handler(upload_book_handler)
    applaction.run_polling()

if __name__ == '__main__':
    db = Database(DB_CONFIG)
    main()