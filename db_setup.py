import os
import logging

import mysql.connector
from mysql.connector import Error, errorcode

from schema import TABLES

DB_NAME = 'book_divination'

logging.basicConfig(level=logging.INFO)


def establish_connection():
    try:
        cnx = mysql.connector.connect(
            host='127.0.0.1',
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'))
        logging.info('connection with mysql is established')
    except Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.critical('invalid login details')
        else:
            logging.critical(err)
        raise err
    return cnx


def create_database(db_name, cursor, character_set='utf8mb4'):
    logging.debug(f"creating database '`{db_name}`'...")
    try:
        cursor.execute(f"CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET {character_set}")
    except Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            logging.warning(f"database `{db_name}` exists")
        else:
            raise err

def use_database(db_name, cursor):
    logging.debug(f"trying to select `{db_name}` as default schema...")
    try:
        cursor.execute(f"USE `{db_name}`")
    except Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error(f"database `{db_name}` does not exists")
        raise err
        
def create_tables(tables, cursor):
    for t in tables:
        try:
            logging.debug(f"creating table `{t}`...")
            cursor.execute(tables[t])
        except Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logging.warning(f"table `{t}` already exists")
            else:
                raise err
            

def setup_database():
    try:
        with establish_connection() as connection:
            cursor = connection.cursor()
            create_database(DB_NAME, cursor)
            use_database(DB_NAME, cursor)
            create_tables(TABLES, cursor)
            logging.info("the database has been configured")
    except Error as err:
        logging.critical(err)

def main():
    logging.getLogger(mysql.connector.__name__).setLevel(logging.WARNING)
    setup_database()

if __name__ == '__main__':
    main()