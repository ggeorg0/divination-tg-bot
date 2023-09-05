import os
import logging
import sys

import mysql.connector
from mysql.connector import Error, errorcode

from schema import CREATE_STATEMENTS, INSERT_STATEMENTS

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

def setup_schema(connection):
    for alias, statement in CREATE_STATEMENTS.items():
        with connection.cursor() as curs:
            logging.info(f'create stage: {alias}')
            curs.execute(statement)
    connection.commit()

def insert_roles(connection):
    for alisas, insertion in INSERT_STATEMENTS.items():
        with connection.cursor() as curs:
            logging.info(f"insertion stage: {alisas}")
            curs.execute(insertion)
    connection.commit()
        

if __name__ == '__main__':
    logging.getLogger(mysql.connector.__name__).setLevel(logging.WARNING)
    with establish_connection() as connection:
        setup_schema(connection)
        insert_roles(connection)