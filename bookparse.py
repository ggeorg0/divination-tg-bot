import os
import logging

import mysql.connector
from mysql.connector import MySQLConnection, Error, errorcode
from typing import List, Optional

from db_setup import establish_connection, use_database, DB_NAME

PAGES_DIR = 'D:/MegaSync/Workspace/Programming/Tgprogs/aconv-bot/notebooks/master_and_margarita'

BOOKS_DIR = './books'

LINE_SYMBOLS = 55
PAGE_SYMBOLS = 50

INSERT_PAGES_QUERY = """INSERT INTO page (book_id, num, content)
VALUES (%s, %s, %s)
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# def insert_book(book, cursor):
#     cursor.execute("SELECT MAX(id) FROM book")
#     max_book_id = cursor.fetchone()[0]
#     if max_book_id:
#         max_book_id = int(max_book_id)
#     else:
#         max_book_id = 0

#     if book['info']:
#         info = f"'{book['info']}'"
#     else:
#         info = 'NULL'

#     cursor.execute(f"INSERT INTO book VALUES ('{max_book_id + 1}', \
#                                               '{book['title']}',   \
#                                               '{book['author']}',  \
#                                               {info})")
#     data_to_insert = [(max_book_id + 1, num + 1, p) for num, p in enumerate(book['pages'])]
#     cursor.executemany(INSERT_PAGES_QUERY, data_to_insert)

# def read_and_insert_books():
#     files = os.listdir(BOOKS_DIR)
#     files = [f for f in files if '.txt' in f] # remove non .txt files

#     with establish_connection() as connection:
#         cursor = connection.cursor()
#         use_database(DB_NAME, cursor)
#         for book_filename in files:
#             logging.info(f'inserting book `{book_filename}`')
#             book = read_book_file(BOOKS_DIR + '/' + book_filename)
#             insert_book(book, cursor)
#             connection.commit()

class Book:
    author: str
    title: str
    info: str
    pages: Optional[List[str]]

    def __init__(self, 
                 author: str = "",
                 title: str = "", 
                 info: str = "", 
                 text: Optional[str] = None):
        logging.info('init new book object')
        self.title = title or "NULL"
        self.author = author or "NULL"
        self.info = info or "NULL"
        if text:
            self.pages = self.pages_from_text(text)
        else:
            self.pages = text       # None

    def __str__(self) -> str:
        return f"'{self.title}', '{self.author}', '{self.info}'"

    def pages_from_text(self, raw_text: str) -> List[str]:
        logging.info('read pages')
        paragraphs = [p for p in raw_text.split('\n') if p]
        lines = [""]
        for p in paragraphs:
            words = p.split()
            self._add_lines(lines, words)
        pages =[[""]]
        for index, line in enumerate(lines):
            pages[-1].append(line)
            if index % PAGE_SYMBOLS == 0:
                pages.append([])
         # list of lines to one string object for each page
        pages = ["\n".join(p) for p in pages]
        return pages

    
    def _add_lines(self, lines, words):
        for w in words:
            if len(lines[-1]) + len(w) < LINE_SYMBOLS:
                if lines[-1]:
                    lines[-1] = lines[-1] + " "
                lines[-1] = lines[-1] + w 
            else:
                lines.append(w)
        lines.append("")    
        return lines


class BookSplitter:
    _book: Book

    def read_book(self, file_path: str) -> Book:
        logging.info(f'reading book {file_path}')
        with open(file_path, "r", encoding='utf-8') as file:
            raw_text = file.readlines()
        self._book = Book(author=raw_text[0].strip(),
                          title=raw_text[1].strip(),
                          info=raw_text[3].strip(),
                          text="".join(raw_text[4:]))
        logging.info(f'readed {file_path}')
        return self._book
    
    @property
    def book(self):
        return self._book 
    
    def insert_into_db(self, 
                       connection: MySQLConnection, 
                       new_book: Optional[Book] = None):
        if not new_book:
            new_book = self._book
        cursor = connection.cursor()
        logging.info('selecting max book id from db')
        cursor.execute("SELECT MAX(id) FROM book")
        max_book_id = cursor.fetchone()
        logging.info(f'select result = "{max_book_id}"')
        if max_book_id and max_book_id[0] != None:
            max_book_id = int(max_book_id[0]) #type: ignore
        else:
            max_book_id = 0
        logging.info(f'max book id = {max_book_id}')
        logging.info('inserting book meta inf')
        cursor.execute(f"INSERT INTO book VALUES ('{max_book_id + 1}', {str(new_book)})")
        logging.info('inserting pages')
        data_to_insert = [(max_book_id + 1, num + 1, p) for num, p in enumerate(new_book.pages)]
        cursor.executemany(INSERT_PAGES_QUERY, data_to_insert)
        logging.info('pages was inserted')

if __name__ == '__main__':
    # read_and_insert_books()
    print('Nothing here')
