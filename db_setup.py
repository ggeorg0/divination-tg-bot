import os
import logging
import sys

import mysql.connector
from mysql.connector import Error, errorcode

from schema import TABLES, CREATE_STATEMENTS

DB_NAME = 'test_bot_db'

logging.basicConfig(level=logging.INFO)


def establish_connection():
    try:
        cnx = mysql.connector.connect(
            host='127.0.0.1',
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'))
        logging.info('connection with mysql server is established')
    except Error as err:
        if err.errno == errorcode.CR_CONN_HOST_ERROR:
            logging.critical("Can't connect to MySQL server")
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.critical('Invqalid login details')
        else:
            raise err
        sys.exit(-1)
    return cnx

# def create_database(db_name, cursor, character_set='utf8mb4'):
#     logging.debug(f"creating database '`{db_name}`'...")
#     try:
#         cursor.execute(f"CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET {character_set}")
#     except Error as err:
#         if err.errno == errorcode.ER_DB_CREATE_EXISTS:
#             logging.warning(f"database `{db_name}` exists")
#         else:
#             raise err

# def use_database(db_name, cursor):
#     logging.debug(f"trying to select `{db_name}` as default schema...")
#     try:
#         cursor.execute(f"USE `{db_name}`")
#     except Error as err:
#         if err.errno == errorcode.ER_BAD_DB_ERROR:
#             logging.error(f"database `{db_name}` does not exists")
#         raise err
        
# def create_tables(tables, cursor):
#     for t in tables:
#         try:
#             logging.debug(f"creating table `{t}`...")
#             cursor.execute(tables[t])
#         except Error as err:
#             if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
#                 logging.warning(f"table `{t}` already exists")
#             else:
#                 raise err

def setup_database():
    with establish_connection() as connection:
        for alias, statement in CREATE_STATEMENTS.items():
            with connection.cursor() as curs:
                logging.info(f'creating {alias}')
                curs.execute(statement)
        connection.commit()

if __name__ == '__main__':
    logging.getLogger(mysql.connector.__name__).setLevel(logging.WARNING)
    setup_database()