import os
from pymongo import MongoClient

def get_db():
    uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/app?replicaSet=rs0")
    client=MongoClient(uri)
    return client.get_default_database()