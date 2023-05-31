import logging
from itertools import count

import mysql.connector
from mysql.connector import MySQLConnection, Error

from bookparse import Book


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
        except Error as e:
            print(e)

    def _validate_connection(self):
        if not self._connection.is_connected():
            self.connect()

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

    def check_for_admin(self, chat_id: int) -> bool:
        self._validate_connection()
        with self._connection.cursor() as cursor:
            cursor.execute(f"SELECT rights FROM chat WHERE id={chat_id}")
            rights = cursor.fetchone()
            # TODO: remove print
            print(rights)
            if rights:
                return rights[0] == 'admin'
        return False

# only for testing Database
# TODO: remove this code later
if __name__ == '__main__':
    from adminbot import DB_CONFIG
    db = Database(DB_CONFIG)
    print(db.check_for_admin(1))
