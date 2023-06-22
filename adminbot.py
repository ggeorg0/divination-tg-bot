import os
from pathlib import Path
import logging

from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, filters
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler

from bookparse import BookReader
from database import Database

BOOKS_DIR = "downloaded_books"

NO_RIGHTS_MSG = "У вас нет прав на использование этого бота."
GREET_MSG = "Добро пожаловать в бот-админку!"
HELP_MSG = """<b>Доступные действия:</b>
- /start
- /stats
- /admins
- /addadmin
- /reconnectdb
- /myid
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
SHOW_ADMINS_MSG = "<b>Список администраторов:</b>\n"
NEW_ADMIN_INSTRUCTIONS_MSG = """Вы хотите добавить нового администратора.
<b>Новый администратор будет иметь все права что и вы.
Используйте эту команду с осторожностью. </b>\n
Напишите id нового администратора.
Чтобы узнать id, используйте /myid
Для отмены добавления напишите /cancel. """
ADMIN_ADDED_MSG = "Администратор добавлен. Для проверки используйте /admins"
INVALID_ID_MSG = "Ошибка добавления нового администатора с таким id. \
Попробуйте ещё раз. Для отмены напишите /cancel"
CANCEL_MSG = "Действие отменено"
FILE_UPLOADED_MSG = "Файл получен. Обработка..."
FILE_DONE_MSG = "Файл загружен в базу данных!"
FILE_ERR_MSG = "Неизвестная ошибка обработки файла."
UNICODE_ERR_MSG = "Ошибка кодировки файла! Используйте UTF-8."
DB_RECONNECT_MSG = "Соединение с базой данных переподключено."
ADD_STATE = 2

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
            return await action(update, context, *args, **kwargs)
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
    
@admin_check
async def show_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admins = db.search_admins()
    await context.bot.send_message(chat_id,
                                   text=SHOW_ADMINS_MSG + str(admins),
                                   parse_mode='HTML')
    
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text=chat_id)

@admin_check
async def new_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, NEW_ADMIN_INSTRUCTIONS_MSG,
                                    parse_mode='HTML')
    return ADD_STATE # ConversationHandler state

# I am going to add separate table to databse with \
# date of granting rights in next versions, so I'll need to change this method.
# And there are no remove_admin method because new admin can remove old one
@admin_check
async def record_new_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        admin_chat_id = int(update.effective_message.text)
    except ValueError:
        await context.bot.send_message(chat_id, INVALID_ID_MSG)
        return ADD_STATE # ConversationHandler state
    db.new_admin(admin_chat_id)
    await context.bot.send_message(chat_id, ADMIN_ADDED_MSG)
    return ConversationHandler.END

@admin_check
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, CANCEL_MSG)
    return ConversationHandler.END

@admin_check
async def reconnect_adminbot_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db.reconnect()
    await context.bot.send_message(chat_id, DB_RECONNECT_MSG)
    

def main():
    applaction = ApplicationBuilder().token(os.environ.get('TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    user_counts_hadler = CommandHandler('stats', users_counts)
    show_admin_handler = CommandHandler('admins', show_admins)
    my_id_handler = CommandHandler('myid', my_id)
    new_admin_handler = ConversationHandler(
        entry_points=[CommandHandler('addadmin', new_admin)],
        states={ADD_STATE: [MessageHandler(filters.TEXT ^ filters.COMMAND, 
                                           record_new_admin)]},
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )
    reconnect_handler = CommandHandler('reconnectdb', reconnect_adminbot_db)
    upload_book_handler = MessageHandler(filters.Document.FileExtension('txt'), new_book)
    
    applaction.add_handlers([
        start_handler,
        help_handler,
        user_counts_hadler,
        my_id_handler,
        show_admin_handler,
        new_admin_handler,
        reconnect_handler,
        upload_book_handler
    ])
    applaction.run_polling()

if __name__ == '__main__':
    db = Database(DB_CONFIG)
    main()