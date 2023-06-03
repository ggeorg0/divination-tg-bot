import logging
from typing import Callable
from itertools import count

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
            cursor.execute(f"SELECT rights FROM chat WHERE id = {chat_id}")
            rights = cursor.fetchone()
            if rights:
                return rights[0] == 'admin'
        return False
    
    @handle_mysql_errors
    def chat_status(self, chat_id: int) -> str | None:
        """
        Search chat status of `chat_id` in MySQL database.

        Returns `'active'`, `'inactive'` or `None` if `chat_id` not found
        """
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT chat_status FROM chat WHERE id = {chat_id}")
            status = cursor.fetchone()
            if status:
                return status[0]
        return None     # chat not exists
    
    @handle_mysql_errors
    def set_chat_active(self, chat_id: int) -> None:
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"UPDATE chat SET chat_status = 'active' \
                           WHERE id={chat_id}")
        self._connection.commit()

    @handle_mysql_errors
    def record_new_chat(self, chat_id: int) -> None:
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO chat (id, chat_status) \
                            VALUES ({chat_id}, 'active')")
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