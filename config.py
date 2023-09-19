import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'database': 'test_bot_db'
}

DOWNLOAD_DIR = "downloaded_books"
