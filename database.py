import logging
from itertools import count

import mysql.connector
from mysql.connector import MySQLConnection, Error

from bookparse import Book

INSERT_PAGES_QUERY = """INSERT INTO page (book_id, num, content)
VALUES (%s, %s, %s)
"""

class Database:
    _ids = count(0)
    connection: MySQLConnection
    config: dict

    def __init__(self, config: dict):
        self.id = next(self._ids)
        if self.id > 1:
            logging.warn(f"there are {self.id} instances of `Database`")
        self.config = config
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.config)
        except Error as e:
            print(e)

    def _validate_connection(self):
        if not self.connection.is_connected():
            self.connect()

    def insert_book(self, book: Book) -> None:
        self._validate_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM book")
            new_book_id = cursor.fetchone()
            if new_book_id and new_book_id[0] != None:
                new_book_id = int(new_book_id[0]) + 1
            else:
                new_book_id = 1
            cursor.execute(f"INSERT INTO book VALUES ('{new_book_id}', {str(book)})")
            marked_pages = [(new_book_id, i + 1, page) for i, page in enumerate(book.pages)]
            cursor.executemany("INSERT INTO page (book_id, num, content)\
                                VALUES (%d, %d, %s)", marked_pages)
        self.connection.commit()
