import os
from datetime import timedelta

from dotenv import load_dotenv
# load environment variables from ".env" file
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'database': 'divination'
}

DOWNLOAD_DIR = "downloaded_books"

# Time between updates of banned users list from database
#  Note: updates are lazy evaluated (when it needs to check user for ban)    
BANLIST_UPD_INTERVAL = timedelta(minutes=2)
