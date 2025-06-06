import os
from dotenv import load_dotenv

load_dotenv()

db_connect_url = os.getenv("DATABASE_CONNECT_URL")

time_zone = os.getenv("TZ")