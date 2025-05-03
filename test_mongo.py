from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = MongoClient(os.getenv("MONGO_URI"))
    dbs = client.list_database_names()
    print("✅ Connected! Available databases:", dbs)
except Exception as e:
    print("❌ Connection failed:", e)
