from fastapi import FastAPI, HTTPException
app = FastAPI()
import os
from dotenv import load_dotenv;
from pymongo import MongoClient
from trino.dbapi import connect as trino_connect
import logging

logger = logging.getLogger("trino_sample")

load_dotenv()

from app.routers import products
from app.routers import denominations
from app.routers import purchase
from app.routers import status

app.include_router(products.router)
app.include_router(denominations.router)
app.include_router(purchase.router)
app.include_router(status.router)

@app.get("/check")
def check():
    return {
        "status": "ok",
        "service": "vending machine"
    }

@app.get("/mongo-ping")
def mongo_ping():
    uri=os.getenv("MONGO_URI")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        return {"ok":True}
    except Exception as e:
        raise HTTPException(status_code=500)
    
@app.get("/trino-ping")
def trino_ping():
    host="localhost"
    port="8080"
    try:
        conn=trino_connect(host=host, port=port, user="surya")
        cur=conn.cursor()
        cur.execute("SHOW CATALOGS")
        catalogs=[row[0] for row in cur.fetchall()]
        return {"ok":True, "catalogs":catalogs}
    except Exception as e:
        raise HTTPException(status_code=500)

@app.get("/trino-sample")
def trino_sample():
    host="localhost"
    port="8080"
    conn=trino_connect(host=host, port=port, user="surya")
    cur=conn.cursor()
    cur.execute("SELECT _id, name, price, qty FROM mongodb.app.products LIMIT 5")
    rows = cur.fetchall()
    return {"rows":rows}

# def fetch_from_mongo(limit=15):
#     client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/app"))
#     db = client.get_default_database()
#     docs = list(db.products.find({}, {"_id":1,"name":1,"price":1,"qty":1,"status":1}).limit(limit))
#     # normalize _id if needed
#     return [{"_id":d["_id"], "name":d.get("name"), "price":d.get("price"), "qty":d.get("qty"), "status":d.get("status")} for d in docs]


# @app.get("/trino-sample")
# def trino_sample():
#     # Try Trino first
#     try:
#         conn = trino_connect()
#         cur = conn.cursor()
#         cur.execute("SHOW CATALOGS")
#         catalogs = [r[0] for r in cur.fetchall()]
#         if "mongodb" not in catalogs:
#             raise RuntimeError(f"mongodb catalog missing in Trino (found: {catalogs})")

#         cur.execute("SELECT _id, name, price, qty, status FROM mongodb.app.products LIMIT 15")
#         rows = cur.fetchall()
#         result = [{"_id": r[0], "name": r[1], "price": r[2], "qty": r[3], "status": r[4]} for r in rows]
#         return {"source": "trino", "rows": result}

#     except Exception as trino_err:
#         # Log full traceback to server logs for debugging
#         logger.exception("Trino failed, falling back to Mongo: %s", trino_err)

#         # Attempt fallback to direct Mongo read
#         try:
#             mongo_rows = fetch_from_mongo(limit=15)
#             return {"source": "mongo_fallback", "rows": mongo_rows, "trino_error": str(trino_err)}
#         except Exception as mongo_err:
#             logger.exception("Fallback to Mongo also failed: %s", mongo_err)
#             # Return a helpful error (dev); in prod log and return generic message
#             raise HTTPException(status_code=502, detail={
#                 "message": "Both Trino and direct Mongo read failed",
#                 "trino_error": str(trino_err),
#                 "mongo_error": str(mongo_err),
#             })