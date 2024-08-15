import logging
import io
import asyncio
from functools import wraps 
from typing import Callable, Set

from telegram import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, filters
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler
from telegram.ext import InvalidCallbackData, Defaults 
import nltk

from database import Database
from imgen import QuoteImage
from config import BOT_TOKEN, DB_CONFIG 


START_MSG = """
Привет! Этот бот позволяет получить предсказание по книге. Прямо как в реальной жизни. Выберите одну из доступных книг (/book), напишите страницу и  желаемую строчку. Вы получите отрывок из книги, который и будет вашим предсказанием!

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
INVALID_BUTTON_MSG = "К сожалению эта кнопка не работает! Попробуйте отправить команду заново."
ERR_VALUE_MSG = "Невозможно выбрать такую книгу. Попробуйте использовать команду заново"
SELECT_PAGE_MSG = "Напишите номер страницы, на которой будет ваше предсказание."
MAX_PAGE_PHRASE = "\nДля вашей книги доступны страницы с <b>1</b> до <b>%s</b>."
SELECT_SENT_MSG = "Отлично! Теперь напишите номер предложения."
MAX_SENT_PHRASE = "\nМожно выбрать предложение с <b>1</b> по <b>%s</b>."
ERR_SELECT_PAGE_MSG = "К сожалению, не получится выбраться страницу с таким номером."
ERR_SELECT_SENT_MSG = "Такого предложения нет на странице, которую вы выбрали."
SUMMARY_BOOK_MESSAGE = "Вы выбрали: <b>{0}</b>\nАвторы: {1}\nОписание: {2}\nВыбрать другую книгу /book"
VERIFY_MSG = "Вы выбрали предложение %s на странице %s."
DIVINATION_MSG = "Ваше предсказание: \n<b>%s</b>"
ERR_NO_PAGE = "Вы не можете выбрать предложение пока не выберите страницу!"
CANCEL_ACTION_MSG = "Действие отменено"
INACCESSIBLE_COMMAND = """Сейчас нельзя использовать такую комманду, так как вы ещё не завершили предыдущее действие. 
Чтобы отменить его, используйте /cancel
"""
BOOK_IS_NULL = "Для начала выбреите книгу с помощью команды /book"
SELECT_BOOK_AGAIN_MSG = "Ой! Мы случайно задели полку и рассыпали все книги! Пожалуйста, выберите книгу заново /book"
NOTHING_CANCEL = "Сейчас нечего отменять."
UNKNOWN_COMMAND = "Неизвестная комманда. Помощь /help"


LIST_H = 3
MAX_BUTTON_CHARS = 50

db: Database
img_generator: QuoteImage 
banned_chats: Set[int]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def check_banned(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update,
                      context: ContextTypes.DEFAULT_TYPE,
                      *args, **kwargs):
        if update.effective_chat.id not in banned_chats:
            return await func(update, context, *args, **kwargs)
        else:
            return ConversationHandler.END
    return wrapper

@check_banned
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_keyboard = ReplyKeyboardRemove()
    if db.check_user_exist(chat_id):
        await context.bot.send_message(chat_id, text=ACTIVE_START_MSG, reply_markup=remove_keyboard)
    else:
        db.record_new_chat(chat_id)
        await context.bot.send_message(chat_id, text=START_MSG, reply_markup=remove_keyboard)

@check_banned
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text=INFO_MSG)

def add_switch_page_buttons(rows: int, desired_rows: int, page_num: int):
    if rows <= desired_rows and page_num == 1:
        return []
    if page_num == 1:
        prev_button = InlineKeyboardButton(" ", callback_data="page_none")
    else:
        prev_button = InlineKeyboardButton(f"Назад | {page_num - 1}",
                                           callback_data=f"page_{page_num - 1}")
    if rows <= desired_rows:
        next_button = InlineKeyboardButton(" ", callback_data="page_none")
    else:
        next_button = InlineKeyboardButton(f"Далее | {page_num + 1}",
                                           callback_data=f"page_{page_num + 1}")
    return [[prev_button, next_button]]

def build_books_menu(book_rows: list, desired_rows: int, page_num: int):
    buttons = []
    for book in book_rows[:desired_rows]:         
        # last rows used as indicator of additional data for page switch buttons
        name = book[1] + ". " + book[2]
        if len(name) > MAX_BUTTON_CHARS:
            name = name[:MAX_BUTTON_CHARS] + "..." 
        buttons.append([InlineKeyboardButton(name, callback_data=f"book_{book[0]}")])
    
    buttons += add_switch_page_buttons(len(book_rows), desired_rows, page_num)
    return InlineKeyboardMarkup(buttons)

def make_books_page(max_rows: int, num: int):
    # last row - indicator of additional data for page switch buttons
    books = db.search_book(rows_count=max_rows+1, 
                           offset=max_rows*(num-1))
    return build_books_menu(books, desired_rows=max_rows, page_num=num)

@check_banned
async def show_first_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    choice_menu = make_books_page(LIST_H, num=1)
    await context.bot.send_message(chat_id, "Выберите книгу", reply_markup=choice_menu)
    return "browse"

@check_banned
async def switch_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.callback_query.data
    if 'page_none' == update.callback_query.data:
        await update.callback_query.answer()
        return "browse"
    page_num = int(choice[5:])
    choice_menu = make_books_page(LIST_H, num=page_num)
    await update.effective_message.edit_reply_markup(choice_menu)
    await update.callback_query.answer()
    return "browse"

def gather_summary_message(title: str, author: str, info: str):
    message = SUMMARY_BOOK_MESSAGE
    if info != 'NULL':
        message = message.format(title, author, info)
    message = message.format(title, author, 'нет описания')
    return message

def gather_maxpage_message(chat_id: int):
    max_page = db.search_max_page(chat_id)
    if max_page == None:
        return SELECT_PAGE_MSG
    return SELECT_PAGE_MSG + MAX_PAGE_PHRASE % max_page

@check_banned
async def set_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.callback_query.data
    chat_id = update.effective_chat.id
    await update.callback_query.answer()
    try:
        book_id = int(choice[5:])
    except ValueError:                      # prevent sql injection
        await update.effective_message.edit_text(ERR_VALUE_MSG)
    else:
        db.update_chat_book(chat_id, book_id)
        book_info = db.book_metadata(book_id)
        await update.effective_message.edit_text(gather_summary_message(*book_info))
        context.chat_data[chat_id] = {"author": book_info[0], "title": book_info[1]}
        await asyncio.sleep(0.5)
        await context.bot.send_message(chat_id, text=gather_maxpage_message(chat_id))
    return ConversationHandler.END

@check_banned
async def select_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in context.chat_data:
        await context.bot.send_message(chat_id, SELECT_BOOK_AGAIN_MSG)
        return ConversationHandler.END
    selected_page = int(update.message.text)
    max_page = db.search_max_page(chat_id)
    if max_page == None:
        await context.bot.send_message(chat_id, ERR_SELECT_PAGE_MSG)
        return ConversationHandler.END 
    if selected_page < 1 or selected_page > max_page:
        message = ERR_SELECT_PAGE_MSG + MAX_PAGE_PHRASE % max_page
        await context.bot.send_message(chat_id, message)
        return ConversationHandler.END
    page_text = db.page_content(chat_id, selected_page)
    sentences = nltk.tokenize.sent_tokenize(page_text, language='russian')
    context.chat_data[chat_id].update({"sentences": sentences, "page": selected_page})
    message = SELECT_SENT_MSG + MAX_SENT_PHRASE % len(sentences)
    await context.bot.send_message(chat_id, message)
    return "browse"

async def send_quote_image(chat_id: int, 
                             quote: str, 
                             context: ContextTypes.DEFAULT_TYPE):
    temp_memory = io.BytesIO()
    img_generator.make(
        context.chat_data[chat_id]["author"], 
        context.chat_data[chat_id]["title"], 
        quote).save(temp_memory, format='png')
    temp_memory.seek(0)
    temp_memory.name = "image.png"
    # await context.bot.send_document(chat_id, temp_memory)
    await context.bot.send_photo(chat_id, temp_memory)
    temp_memory.close() 

@check_banned
async def page_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        page_num = context.chat_data[chat_id]["page"]
        sentences = context.chat_data[chat_id]["sentences"]
        sent_num = int(update.message.text)
        if sent_num < 1 or sent_num > len(sentences):
            raise ValueError
    except KeyError:
        await context.bot.send_message(chat_id, ERR_NO_PAGE)
    except ValueError:
        message = ERR_SELECT_SENT_MSG + MAX_SENT_PHRASE % len(sentences)
        await context.bot.send_message(chat_id, message)
        return "browse"
    else:
        await context.bot.send_message(chat_id, VERIFY_MSG % (sent_num, page_num))
        await asyncio.sleep(1)
        await context.bot.send_message(chat_id, DIVINATION_MSG % sentences[sent_num - 1])
        await send_quote_image(chat_id, sentences[sent_num - 1], context)
        context.chat_data[chat_id].pop("sentences")

    return ConversationHandler.END

@check_banned
async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, CANCEL_ACTION_MSG)
    if chat_id in context.chat_data:
        context.chat_data[chat_id].pop("sentences", None)
    return ConversationHandler.END

@check_banned
async def nothing_to_cancel(update: Update, сontext: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await сontext.bot.send_message(chat_id, NOTHING_CANCEL)

@check_banned
async def default_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, INACCESSIBLE_COMMAND)
    return "browse"

@check_banned
async def command_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, UNKNOWN_COMMAND)

async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informs that button is not available now"""
    await update.callback_query.answer()
    await update.effective_message.edit_text(INVALID_BUTTON_MSG)

async def update_bans(_: ContextTypes.DEFAULT_TYPE):
    banned_chats.update(db.get_banned_users())

def run_bot():
    defaults = Defaults(parse_mode='HTML')
    application = ApplicationBuilder().defaults(defaults)\
                                      .token(BOT_TOKEN)  \
                                      .build()

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

    # update banned users every 5 minutes
    application.job_queue.run_repeating(update_bans, interval=60*5)

    application.run_polling()

if __name__ == '__main__':
    db = Database(DB_CONFIG)
    img_generator = QuoteImage()
    banned_chats = set(db.get_banned_users())
    run_bot()
