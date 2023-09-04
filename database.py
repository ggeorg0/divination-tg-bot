import logging
from typing import Callable, Optional, Sequence
from itertools import count
import datetime

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector import Error, errorcode

from bookparse import Book

# MySQL Errors handling. Used as decorator
def handle_mysql_errors(func: Callable):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as err:
            # TODO
            if err.errno == errorcode.ER_PARSE_ERROR:
                logging.error(f'incorrect SQL syntax')
            elif err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
                logging.error('foreign key constraint fails')
            else:
                logging.error(f'unexpected error: {err}')
            logging.error(f'\t in {func.__name__} args={args}, kwargs={kwargs}')
    return wrapper


class Database:
    _ids = count(0)
    _connection: MySQLConnection
    _config: dict

    def __init__(self, config: dict):
        self.id = next(self._ids)
        if self.id > 1:
            logging.warn(f"there are {self.id} instances of `Database`")
        self._config = config
        self.connect()

    def connect(self):
        try:
            self._connection = mysql.connector.connect(**self._config)
        except Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error('invalid login details')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.error('database does not exsist')
            else:
                logging.error(f'unexpected error: {err} in `Database.connect`')

    def reconnect(self):
        self._connection.reconnect()

    def _validate_connection(self):
        if not self._connection.is_connected():
            self.connect()

    @handle_mysql_errors
    def insert_book(self, book: Book) -> None:
        """Insert data about the book and pages into database."""
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM book")
            new_book_id = cursor.fetchone()
            if new_book_id and new_book_id[0] != None:
                new_book_id = int(new_book_id[0]) + 1
            else:
                new_book_id = 1
            cursor.execute(f"INSERT INTO book VALUES ('{new_book_id}', {str(book)})")
            marked_pages = [(new_book_id, i + 1, page) for i, page in enumerate(book.pages)]
            cursor.executemany("INSERT INTO page (book_id, num, content)\
                                VALUES (%s, %s, %s)", marked_pages)
        self._connection.commit()

    @handle_mysql_errors
    def check_for_admin(self, chat_id: int) -> bool:
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT role_name FROM chat_role_view \
                             WHERE chat_id = {chat_id} \
                             AND role_name = 'admin'")
            if cursor.fetchone():
                return True
        return False
    
    @handle_mysql_errors
    def users_counts(self) -> tuple[int, int, int]:
        """
        Counts bot users

        Returns results in form `(total_count, banned_users, admins)`
        """
        self._validate_connection()
        protect_value = lambda val: 0 if val == None else val[0]
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM chat")
            total = protect_value(cursor.fetchone())
            cursor.execute("SELECT COUNT(*) FROM chat_role_view \
                            WHERE role_name = 'banned'")
            banned = protect_value(cursor.fetchone())
            cursor.execute("SELECT COUNT(*) FROM chat_role_view \
                            WHERE role_name = 'admin'")
            admins = protect_value(cursor.fetchone())
        return (total, banned, admins)

    @handle_mysql_errors
    def search_admins(self) -> list[int]:
        """
        Returns list of admins ids
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT chat_id FROM chat_role_view \
                            WHERE role_name = 'admin'")
            results = cursor.fetchall()
            return [row[0] for row in results]

    @handle_mysql_errors    
    def new_admin(self, chat_id, expire_date: Optional[datetime.date] = None):
        """
        Adds administrator role to given `chat_id` with given `expire_date`.
        If the user is already an admin, expire date is updated 
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(chat_id) FROM chat_role_view \
                             WHERE role_name = 'admin' and chat_id={chat_id}")
            count = cursor.fetchone()
            if count == None or count[0] == 0:
                statement = """INSERT INTO chat_role VALUES (%s,
                               (SELECT id FROM role WHERE name = 'admin'),
                               CURDATE(), %s)"""
                data = (chat_id, expire_date)
            else:
                statement = """UPDATE chat_role SET expire_date = %s
                               WHERE chat_id = %s AND 
                               role_id = (SELECT id FROM role WHERE name = 'admin')"""
                data = (expire_date, chat_id)
            cursor.execute(statement, data)
        self._connection.commit()
    
    @handle_mysql_errors
    def check_user_exist(self, chat_id: int) -> bool:
        """
        Search user with given `chat_id` in database

        Returns `True` if user exists
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM chat \
                             WHERE id = {chat_id}")
            count = cursor.fetchone()
            if count != None and count[0] == 1:
                return True
        return False

    @handle_mysql_errors
    def get_banned_users(self) -> Sequence[int]:
        """
        Search user's chats with role 'banned' in database.
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT chat_id FROM chat_role_view \
                             WHERE role_name = 'banned'")
            return [row[0] for row in cursor.fetchall()]

    @handle_mysql_errors
    def record_new_chat(self, chat_id: int) -> None:
        """
        Insert new chat into database

        When chat with given id already exists an
        'incorrect SQL syntax' exeption occurs.
        Exception handled by internal function `database.handle_mysql_errors`
        and returns `None`
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO chat (id) \
                            VALUES ({chat_id})")
        self._connection.commit()

    @handle_mysql_errors
    def search_book(self, rows_count: int, offset: int = 0):
        """
        Get list of available books in pairs (title, author)
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT id, title, author FROM book \
                           ORDER BY id LIMIT {offset}, {rows_count}")
            return cursor.fetchall()
        
    @handle_mysql_errors
    def search_max_page(self, chat_id: int):
        """
        Returns max page number of user's book
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT MAX(num) FROM page WHERE book_id = \
                           (SELECT book_id FROM chat WHERE id = {chat_id})")
            max_page = cursor.fetchone()
            if max_page != None:
                return max_page[0]
        return None 
    
    @handle_mysql_errors
    def update_chat_book(self, chat_id: int, book_id):
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"UPDATE chat SET book_id = {book_id} \
                            WHERE id = {chat_id}")
        self._connection.commit()

    @handle_mysql_errors
    def book_metadata(self, book_id: int):
        """
        Get book metadata: title, author, description
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT title, author, info \
                           FROM book WHERE id = {book_id}")
            metadata = cursor.fetchone()
            return metadata
    
    @handle_mysql_errors
    def page_content(self, chat_id: int, page_num: int):
        """
        Text of page with number=`page_num` from user's book
        with chat_id=`chat_id`
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT content FROM page WHERE \
                            num = {page_num} AND book_id = \
                            (SELECT book_id FROM chat WHERE id = {chat_id})")
            page_text = cursor.fetchone()
            if page_text != None:
                return page_text[0]
        return None
    

if __name__ == '__main__':
    logging.warning("To run the bot, use a different .py file. \
This class is needed only to communicate with the database.")
