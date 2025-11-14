import os
from pymongo import MongoClient, UpdateOne

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/app?replicaSet=rs0")
client = MongoClient(MONGO_URI)
db = client.get_default_database()

products = [
    {
        "_id": 101,
        "name": "Chips",
        "price": 25,
        "qty": 10,
        "status": "Available",
        "category": "Snacks",
        "description": "Classic salted potato chips",
    },
    {
        "_id": 102,
        "name": "Soda",
        "price": 40,
        "qty": 8,
        "status": "Available",
        "category": "Beverages",
        "description": "Carbonated soft drink (300ml)",
    },
    {
        "_id": 103,
        "name": "Chocolate",
        "price": 30,
        "qty": 0,
        "status": "Sold Out",
        "category": "Sweets",
        "description": "Milk chocolate bar (45g)",
    },
    {
        "_id": 104,
        "name": "Cookies",
        "price": 35,
        "qty": 5,
        "status": "Available",
        "category": "Bakery",
        "description": "Choco-chip cookies (pack of 4)",
    },
    {
        "_id": 105,
        "name": "Chips2",
        "price": 25,
        "qty": 10,
        "status": "Available",
        "category": "Snacks",
        "description": "Classic salted potato chips",
    },
    {
        "_id": 106,
        "name": "Soda2",
        "price": 40,
        "qty": 8,
        "status": "Available",
        "category": "Beverages",
        "description": "Carbonated soft drink (300ml)",
    },
    {
        "_id": 107,
        "name": "Chocolate2",
        "price": 30,
        "qty": 0,
        "status": "Sold Out",
        "category": "Sweets",
        "description": "Milk chocolate bar (45g)",
    },
    {
        "_id": 108,
        "name": "Cookies2",
        "price": 35,
        "qty": 5,
        "status": "Available",
        "category": "Bakery",
        "description": "Choco-chip cookies (pack of 4)",
    },
    {
        "_id": 109,
        "name": "Chips3",
        "price": 25,
        "qty": 10,
        "status": "Available",
        "category": "Snacks",
        "description": "Classic salted potato chips",
    },
    {
        "_id": 110,
        "name": "Soda3",
        "price": 40,
        "qty": 8,
        "status": "Available",
        "category": "Beverages",
        "description": "Carbonated soft drink (300ml)",
    },
    {
        "_id": 111,
        "name": "Chocolate3",
        "price": 30,
        "qty": 0,
        "status": "Sold Out",
        "category": "Sweets",
        "description": "Milk chocolate bar (45g)",
    },
    {
        "_id": 112,
        "name": "Cookies3",
        "price": 35,
        "qty": 5,
        "status": "Available",
        "category": "Bakery",
        "description": "Choco-chip cookies (pack of 4)",
    }
]

db.products.bulk_write(
    [UpdateOne({"_id": p["_id"]}, {"$set": p}, upsert=True) for p in products]
)

drawer = {
    "_id": "INR",
    "denoms": [
        {"value": 1, "count": 50},
        {"value": 2, "count": 50},
        {"value": 5, "count": 50},
        {"value": 10, "count": 50},
        {"value": 20, "count": 50},
        {"value": 50, "count": 50},
        {"value": 100, "count": 50},
        {"value": 200, "count": 50},
    ],
}

db.cash_drawer.update_one({"_id": "INR"}, {"$set": drawer}, upsert=True)

print("Seed complete.")


# # trino-minikube-values.yaml
# coordinator:
#   replicas: 1
#   service:
#     type: NodePort
#   resources:
#     requests:
#       cpu: "0.5"
#       memory: "1024Mi"
#     limits:
#       cpu: "1"
#       memory: "2048Mi"

# worker:
#   replicas: 1
#   resources:
#     requests:
#       cpu: "0.5"
#       memory: "1024Mi"
#     limits:
#       cpu: "1"
#       memory: "2048Mi"

# persistence:
#   enabled: false   # ephemeral for local testing

# service:
#   type: NodePort
