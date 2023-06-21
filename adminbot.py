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
HELP_MSG = """<b>Доступные действия:</b>
- /start
- /stats
- /logs
- /help

Чтобы загрузить книгу. Отправьте файл с расширением .txt.
Первые четыре строчки файла должы содержать:<i>
    Авторы.
    Название.
    [пустая строка]
    Описание/Аннотация.</i>
"""
COUNTS_MSG = """<b>Статистика по чатам:</b>
Всего чатов: {}
Активные: {}
Админы: {}
"""
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

db: Database

def admin_check(action):
    async def wrapper(update: Update, 
                      context: ContextTypes.DEFAULT_TYPE, 
                      *args, **kwargs):
        chat_id = update.effective_chat.id
        if db.check_for_admin(chat_id):
            await action(update, context, *args, **kwargs)
        else:
            await context.bot.send_message(chat_id, text=NO_RIGHTS_MSG) 
    return wrapper

@admin_check
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id, 
                                   text=GREET_MSG)

@admin_check    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   text=HELP_MSG,
                                   parse_mode='HTML')

async def download_file(message: Message) -> Path:
    attachment = message.effective_attachment
    new_file = await attachment.get_file()
    download_path = Path(BOOKS_DIR, attachment.file_name)
    await new_file.download_to_drive(download_path)
    return download_path

@admin_check
async def new_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """upload book in .txt fromat to database"""
    chat_id = update.effective_chat.id
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

@admin_check
async def see_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """see application logs !Not implemented yet"""
    pass

@admin_check
async def users_counts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """sends message with number of users"""
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id,
                                   text=COUNTS_MSG.format(*db.users_counts()),
                                   parse_mode='HTML')

def main():
    applaction = ApplicationBuilder().token(os.environ.get('TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    user_counts_hadler = CommandHandler('stats', users_counts)
    upload_book_handler = MessageHandler(filters.Document.FileExtension('txt'), new_book)
    
    applaction.add_handler(start_handler)
    applaction.add_handler(help_handler)
    applaction.add_handler(user_counts_hadler)
    applaction.add_handler(upload_book_handler)
    applaction.run_polling()

if __name__ == '__main__':
    db = Database(DB_CONFIG)
    main()