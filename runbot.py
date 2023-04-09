import logging
import os
import asyncio

from telegram import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, filters
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, InvalidCallbackData
import mysql.connector
from mysql.connector import Error, errorcode
import nltk

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'database': 'book_divination'
}

START_MSG = """
Привет! Этот бот позволяет получить предсказание по книге. Выберите одну из доступных книг (/book), напишите страницу и  желаемую строчку. Вы получите отрывок из книги, который и будет вашим предсказанием!

<i>Больше информации и помощь: </i> /help
"""
INFO_MSG = """Этот бот позволяет получить предсказание по книге.

<b>Работа с ботом:</b>
1. Для начала вам нужно выбрать книгу
    /book — выводит список доступных книг. 
Вам необязательно каждый раз заново выбирать книгу, вы можете сделать это один раз.
2. После того как вы выбрали книгу, можно получить предсказание. Для этого отправьте сообщение с номером страницы, к примеру <i>109</i>. 
Затем отправьте номер предложения, например <i>17</i>. 
Вы получите отрывок из книги, который и будет вашим предсказанием.
3. После того как вы получили предсказание, вы можете получить ещё одно: просто напишите номер страницы и следуйте инструкциям из предыдущего пункта, кроме того вы можете выбрать другую книгу.

<b>Список команд:</b>
/start — начало работы с ботом.
/book — выводит список доступных книг.
/cancel — отмена предыдущего действия. Например, вы написали команду /book, а потом передумали.
/help — показать это сообщение

Связь @nvrmnb
"""
ACTIVE_START_MSG = "Предлагаем вам выбрать понравившуюся книгу и получить предсказание! Помощь /help"
INACTIVE_START_MSG = "Рады видеть вас снова! Помощь /help"
ERR_MSG = "Случилась ошибка! Не переживайте, мы обязательно все починим. \nerr. code: %d "
INVALID_BUTTON_MSG = "К сожалению эта кнопка не работает! Попробуйте отправить команду заново."
ERR_VALUE_MSG = "Невозможно выбрать такую книгу. Попробуйте использовать команду заново"
SELECT_PAGE_MSG = "Напишите номер страницы, на которой будет ваше предсказание."
MAX_PAGE_PHRASE = "\nДля вашей книги доступны страницы с <b>1</b> до <b>%s</b>."
SELECT_SENT_MSG = "Отлично! Теперь напишите номер предложения."
MAX_SENT_PHRASE = "\nМожно выбрать предложение с <b>1</b> по <b>%s</b>."
ERR_SELECT_PAGE_MSG = "К сожалению, не получится выбраться страницу с таким номером."
ERR_SELECT_SENT_MSG = "Такого предложения нет на странице, которую вы выбрали."
VERIFY_MSG = "Вы выбрали предложение %s на странице %s."
DIVINATION_MSG = "Ваше предсказание: \n<b>%s</b>"
ERR_NO_PAGE = "Вы не можете выбрать предложение пока не выберите страницу!"
CANCEL_ACTION_MSG = "Действие отменено"
INACCESSIBLE_COMMAND = """Сейчас нельзя использовать такую комманду, так как вы ещё не завершили предыдущее действие. 
Чтобы отменить его, используйте /cancel
"""
BOOK_IS_NULL = "Для начала выбреите книгу с помощью команды /book"
NOTHING_CANCEL = "Сейчас нечего отменять."
UNKNOWN_COMMAND = "Неизвестная комманда. Помощь /help"


LIST_H = 3
MAX_BUTTON_CHARS = 50


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def make_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error('invalid login details')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error('database does not exsist')
        else:
            logging.error(f'unexpected error: {err} in `make_db_connection`')
        raise err

def search_chat_status(chat_id: int, connection: mysql.connector.MySQLConnection):
    """search chat status of `chat_id` in MySQL database.
    If `chat_id` was not found, then a new entry is made to the database
    
    Return 'active', 'inactive' or `None`"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM chat WHERE id = {chat_id}")
        entries_count = cursor.fetchone()[0]
        if entries_count == 1:
            cursor.execute(f"SELECT chat_status FROM chat WHERE id = {chat_id}")
            return cursor.fetchone()[0]
        return None
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `search_chat_status`')
        else:
            logging.error(f'unexpected error: {err} in `search_chat_status`')      # TODO
        raise err

def record_new_chat(chat_id: int, connection: mysql.connector.MySQLConnection):
    try:
        cursor = connection.cursor()
        cursor.execute(f"INSERT INTO chat (id, chat_status) VALUES ({chat_id}, 'active')")
        connection.commit()
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `record_new_chat`')
        else:
            logging.error(f'unexpected error: {err} in `record_new_chat`')      # TODO
        raise err
    
def update_chat_status(chat_id: int, connection: mysql.connector.MySQLConnection):
    try:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE chat SET chat_status = 'active' WHERE id = {chat_id}")
        connection.commit()
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `update_chat_status`')
        else:
            logging.error(f'unexpected error: {err} in `update_chat_status`')      # TODO
        raise err

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_keyboard = ReplyKeyboardRemove()
    try:
        with make_db_connection() as connection:
            status = search_chat_status(chat_id, connection)
            if status == 'active':
                await context.bot.send_message(chat_id, text=ACTIVE_START_MSG, reply_markup=remove_keyboard)
            elif status == 'inactive':
                update_chat_status(chat_id, connection)
                await context.bot.send_message(chat_id, text=INACTIVE_START_MSG, reply_markup=remove_keyboard)
            else:
                record_new_chat(chat_id, connection)
                await context.bot.send_message(chat_id, text=START_MSG, reply_markup=remove_keyboard)
    except Error as err:
        await context.bot.send_message(chat_id, text=ERR_MSG % err.errno)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text=INFO_MSG, parse_mode='HTML')
    
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardRemove()
    await context.bot.send_message(chat_id=update.effective_chat.id, text='')


def add_switch_page_buttons(rows: int, desired_rows: int, page_num: int):
    if rows <= desired_rows and page_num == 1:
        return []
    if page_num == 1:
        prev_button = InlineKeyboardButton(" ", callback_data="page_none")
    else:
        prev_button = InlineKeyboardButton(f"Назад ⬅️ ({page_num - 1})",
                                           callback_data=f"page_{page_num - 1}")
    if rows <= desired_rows:
        next_button = InlineKeyboardButton(" ", callback_data="page_none")
    else:
        next_button = InlineKeyboardButton(f"Далее ➡️ ({page_num + 1})",
                                           callback_data=f"page_{page_num + 1}")
    return [[prev_button, next_button]]

def build_books_menu(book_rows: list, desired_rows: int, page_num: int):
    buttons = []
    for book in book_rows[:desired_rows]:         # last rows used as indicator of additional data for page switch buttons
        name = book[1] + ". " + book[2]
        if len(name) > MAX_BUTTON_CHARS:
            name = name[:MAX_BUTTON_CHARS] + "..." 
        buttons.append([InlineKeyboardButton(name, callback_data=f"book_{book[0]}")])
    
    buttons += add_switch_page_buttons(len(book_rows), desired_rows, page_num)
    return InlineKeyboardMarkup(buttons)

def search_books(connection: mysql.connector.MySQLConnection, rows_count: int, offset: int = 0): # make connection argument first in other functions
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT id, title, author FROM book ORDER BY id LIMIT {offset}, {rows_count}")
        return cursor.fetchall()
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `update_chat_status`')
        else:
            logging.error(f'unexpected error: {err} in `update_chat_status`')      # TODO
        raise err

def make_books_page(max_rows: int, num: int):
    with make_db_connection() as connection:
        books = search_books(connection, 
                            rows_count=max_rows+1,     # last row - indicator of additional data for page switch buttons
                            offset=max_rows*(num-1)) 
    return build_books_menu(books, desired_rows=max_rows, page_num=num)
    
async def show_first_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('in `show_first_page`')
    chat_id = update.effective_chat.id
    try:
        choice_menu = make_books_page(LIST_H, num=1)
        await context.bot.send_message(chat_id, "Выберите книгу", reply_markup=choice_menu)
    except Error as err:
        await context.bot.send_message(chat_id, ERR_MSG % err.errno)
    return "browse"

async def switch_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.callback_query.data
    chat_id = update.effective_chat.id
    logging.info(f'int `switch_page`: {choice}')
    if 'page_none' == update.callback_query.data:
        await update.callback_query.answer()
        return "browse"
    page_num = int(choice[5:])
    try:
        choice_menu = make_books_page(LIST_H, num=page_num)
        await update.effective_message.edit_reply_markup(choice_menu)
    except Error as err:
        await context.bot.send_message(chat_id, ERR_MSG % err.errno)
    await update.callback_query.answer()
    return "browse"


def update_chat_book(connection: mysql.connector.MySQLConnection, chat_id: int, book_id: int):
    try:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE chat SET book_id = {book_id} WHERE id = {chat_id}")
        connection.commit()
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `update_chat_book`')
        elif err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            logging.error('book id foreign key constraint fails in `update_chat_book`')
        else:
            logging.error(f'unexpected error: {err} in `update_chat_book`')
        raise err
    
def search_book_info(connection: mysql.connector.MySQLConnection, book_id: int):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT title, author, info FROM book WHERE id = {book_id}")
        return cursor.fetchone()
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error('incorrect SQL syntax in `search_book_info`')
        else:
            logging.error(f'unexpected error: {err} in `search_book_info`')
        raise err

def gather_summary_message(title: str, author: str, info: str):
    message = "Вы выбрали: <b>{0}</b>\nАвторы: {1}\nОписание: {2}\nВыбрать другую книгу /book"
    if info:
        message =  message.format(title, author, info)
    message = message.format(title, author, 'нет описания')
    return message

def search_max_page(connection: mysql.connector.MySQLConnection, chat_id: int):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(num) FROM page WHERE book_id = \
                        (SELECT book_id FROM chat WHERE id = {chat_id})")
        return cursor.fetchone()[0]
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error(f'incorrect SQL syntax in `search_max_page`')
        else:
            logging.error(f'unexpected error: {err} in `search_max_page`')
        raise err

def gather_maxpage_message(chat_id: int):
    try:
        with make_db_connection() as connection:
            max_page = search_max_page(connection, chat_id)
    except Error as err:
        # we send message without telling client that something has gone wrong 
        # in case it's temporary failure in database 
        # and we can continue using mysql connector later
        return SELECT_PAGE_MSG 
    return SELECT_PAGE_MSG + MAX_PAGE_PHRASE % max_page


async def set_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.callback_query.data
    chat_id = update.effective_chat.id
    logging.info(f'int `set_book`: {choice}')
    await update.callback_query.answer()
    try:
        book_id = int(choice[5:])
        with make_db_connection() as connection:
            update_chat_book(connection, chat_id, book_id)
            book_info = search_book_info(connection, book_id)
    except ValueError:                      # prevent sql injection
        await update.effective_message.edit_text(ERR_VALUE_MSG)
    except Error as err:
        await context.bot.send_message(chat_id, ERR_MSG % err.errno)
    else:
        await update.effective_message.edit_text(gather_summary_message(*book_info),
                                                 parse_mode='HTML')
        await asyncio.sleep(0.5)
        await context.bot.send_message(chat_id, text=gather_maxpage_message(chat_id), 
                                       parse_mode='HTML')

    return ConversationHandler.END

def search_page_content(connection: mysql.connector.MySQLConnection, chat_id: int, page: int):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT content FROM page WHERE \
                       num = {page} AND \
                       book_id = (SELECT book_id FROM chat WHERE id = {chat_id})")
        return nltk.tokenize.sent_tokenize(cursor.fetchone()[0], language='russian')
    except Error as err:
        if err.errno == errorcode.ER_PARSE_ERROR:
            logging.error(f'incorrect SQL syntax in `search_page_content`')
        else:
            logging.error(f'unexpected error: {err} in `search_page_content`')
        raise err

async def select_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('in `select_page`')
    chat_id = update.effective_chat.id
    selected_page = int(update.message.text)
    try:
        with make_db_connection() as connection:
            max_page = search_max_page(connection, chat_id)
            if max_page == None:
                raise TypeError
            if selected_page < 1 or selected_page > max_page:
                raise ValueError
            max_sent = len(search_page_content(connection, chat_id, selected_page))
    except (Error, ValueError, TypeError) as ex:
        if isinstance(ex, Error):
            await context.bot.send_message(chat_id, ERR_MSG % ex.errno)
        if isinstance(ex, TypeError):
            await context.bot.send_message(chat_id, )
        if isinstance(ex, ValueError):
            await context.bot.send_message(chat_id, ERR_SELECT_PAGE_MSG + MAX_PAGE_PHRASE % max_page,
                                           parse_mode='HTML')
        return ConversationHandler.END
    context.chat_data[chat_id] = selected_page
    await context.bot.send_message(chat_id, SELECT_SENT_MSG + MAX_SENT_PHRASE % max_sent,
                                   parse_mode='HTML')
    return "browse"

async def page_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('int `page_line`')
    chat_id = update.effective_chat.id
    sent_num = int(update.message.text)
    try:
        page_num = context.chat_data[chat_id]
        with make_db_connection() as connection:
            sents = search_page_content(connection, chat_id, page_num)
        if sent_num < 1 or sent_num > len(sents):
            raise ValueError
    except KeyError:
        await context.bot.send_message(chat_id, ERR_NO_PAGE)
    except ValueError:
        await context.bot.send_message(chat_id, 
                                       ERR_SELECT_SENT_MSG + MAX_SENT_PHRASE % len(sents),
                                       parse_mode='HTML')
        return "browse"
    except Error as err:
        await context.bot.send_message(chat_id, ERR_MSG % err.errno)
    else:
        await context.bot.send_message(chat_id, VERIFY_MSG % (sent_num, page_num))
        await asyncio.sleep(1)
        await context.bot.send_message(chat_id, DIVINATION_MSG % sents[sent_num - 1], parse_mode='HTML')
        context.chat_data.pop(chat_id, None)

    return ConversationHandler.END

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('in `cancel_action`')
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, CANCEL_ACTION_MSG)
    return ConversationHandler.END

async def nothing_to_cancel(update: Update, сontext: ContextTypes.DEFAULT_TYPE):
    logging.info('in `nothing_to_cancel`')
    chat_id = update.effective_chat.id
    await сontext.bot.send_message(chat_id, NOTHING_CANCEL)

async def default_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('in `default_error`')
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, INACCESSIBLE_COMMAND)
    return "browse"

async def command_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('in ``command_not_found')
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, UNKNOWN_COMMAND)

async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информирует пользователя о том, что кнопка больше недоступна"""
    logging.info('in `handle_invalid_button`')
    await update.callback_query.answer()
    await update.effective_message.edit_text(INVALID_BUTTON_MSG)

def main():
    application = ApplicationBuilder().token(os.environ.get('TOKEN')).build()

    start_handler = CommandHandler('start', start)

    help_handler = CommandHandler('help', help)

    select_book_handler = ConversationHandler(
        entry_points=[CommandHandler('book', show_first_page)],
        states={
            "browse": [CallbackQueryHandler(switch_page, pattern='page_\w+'),
                       CallbackQueryHandler(set_book, pattern='book_\d+')]
                },
        fallbacks=[CommandHandler('cancel', cancel_action),
                   MessageHandler(filters.TEXT | filters.COMMAND, default_error)], 
        per_message=False)
    
    make_divitaion_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^\s*\d+\s*$'), select_page)],
        states={
            "browse": [MessageHandler(filters.Regex(r'^\s*\d+\s*$'), page_line)]
                },
        fallbacks=[CommandHandler('cancel', cancel_action), 
                   MessageHandler(filters.TEXT | filters.COMMAND, default_error)],
        per_message=False)
    
    useless_cancel_handler = CommandHandler('cancel', nothing_to_cancel)
    
    unknown_command_handler = MessageHandler(filters.TEXT | filters.COMMAND, command_not_found)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(select_book_handler)
    application.add_handler(make_divitaion_handler)
    application.add_handler(useless_cancel_handler)
    application.add_handler(unknown_command_handler)

    application.add_handler(CallbackQueryHandler(handle_invalid_button))

    application.run_polling()


if __name__ == '__main__':
    main()
