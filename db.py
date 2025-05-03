# db.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["psychiq"]
collection = db["patients"]

def insert_patient(name: str, symptoms: str, urgency: str):
    patient = {
        "name": name,
        "symptoms": symptoms,
        "urgency": urgency
    }
    collection.insert_one(patient)

def get_all_patients():
    return list(collection.find({}, {"_id": 0}))  # hide Mongo's internal _id
