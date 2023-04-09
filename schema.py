import logging
import sys

WARN_MSG = """built-in dict class has the ability to remember insertion order in Python 3.7 or above, 
your Python version is %s.%s.%s. It means the table creation order may be incorrect."""

TABLES = {}

TABLES['book'] = """
CREATE TABLE book(
    id SMALLINT UNSIGNED NOT NULL,
    title VARCHAR(1024),
    author VARCHAR(1024),
    info VARCHAR(2048),
    PRIMARY KEY (id)
)
"""
       
TABLES['chat'] = """
CREATE TABLE chat(
    id BIGINT UNSIGNED PRIMARY KEY,
    chat_status ENUM('active', 'inactive') NOT NULL,
    rights ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    book_id SMALLINT UNSIGNED NULL,
    FOREIGN KEY (book_id) 
        REFERENCES book(id)
)"""
       
TABLES['page'] = """
CREATE TABLE page(
    book_id SMALLINT UNSIGNED,
    num MEDIUMINT UNSIGNED,
    content VARCHAR(4096),
    PRIMARY KEY (book_id, num),
    FOREIGN KEY (book_id)
        REFERENCES book (id)
)"""


ver = sys.version_info
if ver[0] < 3 or ver[1] < 7:
    logging.warning(WARN_MSG % (ver[0], ver[1], ver[2]))