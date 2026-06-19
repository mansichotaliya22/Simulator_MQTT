import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME


class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[MONGO_COLLECTION_NAME]

    def insert_data(self, data):
        return self.collection.insert_one(data)

    def fetch_latest(self, limit=20):
        return list(
            self.collection.find().sort("_id", -1).limit(limit)
        )

    def find_one(self, query):
        return self.collection.find_one(query)

    def count_documents(self):
        return self.collection.count_documents({})
