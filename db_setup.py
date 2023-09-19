import os
import logging
import sys

import mysql.connector
from mysql.connector import Error, errorcode

from schema import (
    TABLES_CREATION, 
    ROLE_INSERTIONS,
    ADMIN_INSERTION
)

logging.basicConfig(level=logging.INFO)


def establish_connection():
    try:
        cnx = mysql.connector.connect(
            host='127.0.0.1',
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            autocommit=True)
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
    for alias, statement in TABLES_CREATION.items():
        with connection.cursor() as curs:
            logging.info(f'create stage: {alias}')
            curs.execute(statement)

def insert_roles(connection):
    for alisas, insertion in ROLE_INSERTIONS.items():
        with connection.cursor() as curs:
            logging.info(f"insertion stage: {alisas}")
            curs.execute(insertion)

def insert_admin(connection):
    admin_id = input("\nEnter id of the first admin (or press Enter for skip): ")
    if admin_id.strip():
        logging.info(f"inserting admin with id {admin_id}")
        for alias, statement in ADMIN_INSERTION.items():
            with connection.cursor() as curs:
                logging.info(f"admin insertion: {alias}")
                curs.execute(statement.format(admin_id))
    else:
        logging.info("skiping admin insertion")


if __name__ == '__main__':
    logging.getLogger(mysql.connector.__name__).setLevel(logging.WARNING)
    with establish_connection() as connection:
        setup_schema(connection)
        insert_roles(connection)
        insert_admin(connection)
        logging.info("Done.")