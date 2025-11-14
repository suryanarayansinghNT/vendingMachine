from typing import List, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Request
import random
from pydantic import BaseModel
from trino.exceptions import TrinoQueryError
import time
from app.trino_client import get_trino_conn
from app.db import get_db
from pymongo import ReturnDocument

router = APIRouter(prefix="/purchase", tags=["purchase"])

class PurchaseRequest(BaseModel):
    snack_id: int
    cash_amount: int
    quantity: int = 1

class ChangeItem(BaseModel):
    value: int
    count: int

class PurchaseResponse(BaseModel):
    snack_id: int
    price: int
    change: List[ChangeItem]
    remaining_qty: int

def compute_change(amount:int, denoms:List[Dict]) -> Optional[List[Dict]]:
    denoms_sorted=sorted(denoms,key=lambda d: d["value"],reverse=True)
    target=amount
    solution=[0]*len(denoms_sorted)

    def backtrack(i, remaining):
        if remaining==0:
            return True
        if i>=len(denoms_sorted):
            return False
        v = denoms_sorted[i]["value"]
        max_use = min(denoms_sorted[i]["count"],remaining // v)
        for use in range(max_use, -1, -1):
            solution[i]=use
            if backtrack(i + 1,remaining-use*v):
                return True
        solution[i] = 0
        return False

    if target==0:
        return []

    ok=backtrack(0,target)

    if not ok:
        return None

    result=[]

    for idx, used in enumerate(solution):
        if used:
            result.append({"value":denoms_sorted[idx]["value"],"count":used})
    return result

def trino_get_product(snack_id: int):

    sql = (
        'select "_id", price, qty, status '
        "from mongodb.app.products "
        f'where "_id" = {int(snack_id)}'
    )

    try:
        with get_trino_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
    except TrinoQueryError as e:
        raise HTTPException(status_code=502, detail="trino failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail="internal error read")

    if not rows:
        return None
    
    r = rows[0]
    return {"_id": int(r[0]), "price":int(r[1]), "qty":int(r[2]),"status":r[3]}

def trino_get_drawer(currency: str = "INR"):
    sql = "select _id, denoms from mongodb.app.cash_drawer where _id = '%s'" % currency
    try:
        with get_trino_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
    except TrinoQueryError:
        raise HTTPException(status_code=502, detail="trino query failed")
    except Exception:
        raise HTTPException(status_code=500, detail="internal error reading drawer")
    if not rows:
        return None
    
    _id, denoms_raw = rows[0][0], rows[0][1] or []

    denoms = []

    for d in denoms_raw:
        if isinstance(d, dict):
            val = d.get("value"); cnt = d.get("count")
        elif isinstance(d, (list, tuple)) and len(d) >= 2:
            val, cnt = d[0], d[1]
        else:
            val = getattr(d, "value", None); cnt = getattr(d, "count", None)
        denoms.append({"value": int(val), "count": int(cnt)})
    return {"_id": _id, "denoms": denoms}

def get_idempotent_result(db, key:str):
    return db.idempotency.find_one({"_id":key})

def save_idempotent_result(db, key:str, response_doc:Dict):
    db.idempotency.update_one({"_id":key}, {"$set": {"response":response_doc,"ts":time.time()}}, upsert=True)

@router.post("", response_model=PurchaseResponse)
def purchase(request:PurchaseRequest, Idempotency_Key:Optional[str] = Header(None)):
    if request.cash_amount <= 0:
        raise HTTPException(status_code=400, detail="cash amount not positive")
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")

    db = get_db()

    if Idempotency_Key:
        prev = get_idempotent_result(db, Idempotency_Key)
        if prev:
            return prev["response"]

    prod = trino_get_product(request.snack_id)
    if not prod:
        raise HTTPException(status_code=404, detail="product not found")

    unit_price = int(prod["price"])
    quantity = int(request.quantity)
    total_price = unit_price * quantity

    if request.cash_amount < total_price:
        raise HTTPException(status_code=400, detail={"error":"insufficient cash", "refund":request.cash_amount})

    if prod["qty"] < quantity or prod["status"] != "Available":
        raise HTTPException(status_code=409, detail={"error":"out of stock", "refund":request.cash_amount})

    change_amount = request.cash_amount - total_price

    if change_amount == 0:
        updated = db.products.find_one_and_update(
            {"_id": request.snack_id, "qty":{"$gte": quantity}},
            {"$inc": {"qty": -quantity}},
            return_document=ReturnDocument.AFTER,
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"error":"out of stock", "refund":request.cash_amount})
        if updated.get("qty", 0) == 0:
            db.products.update_one({"_id": request.snack_id, "qty": 0}, {"$set": {"status": "Sold Out"}})
        tx = {
            "snack_id":request.snack_id,
            "unit_price": unit_price,
            "quantity": quantity,
            "price": total_price,
            "cash_in":request.cash_amount,
            "change":[],
            "status":"SUCCESS",
            "ts":time.time()
        }
        db.transactions.insert_one(tx)
        resp = {"snack_id":request.snack_id, "price":total_price, "change":[], "remaining_qty":updated.get("qty", 0)}
        if Idempotency_Key:
            save_idempotent_result(db, Idempotency_Key, resp)
        return resp

    drawer = trino_get_drawer("INR")
    if not drawer:
        raise HTTPException(status_code=500,detail="cash drawer not initialized")
    denoms = drawer["denoms"]

    max_retries = 3
    for attempt in range(max_retries):
        combo = compute_change(change_amount, denoms)
        if combo is None:
            raise HTTPException(status_code=409, detail={"error":"CHANGE_UNAVAILABLE", "refund":request.cash_amount})

        updated_product = db.products.find_one_and_update(
            {"_id":request.snack_id, "qty":{"$gte": quantity}},
            {"$inc": {"qty": -quantity}},
            return_document=ReturnDocument.AFTER,
        )
        if not updated_product:
            raise HTTPException(status_code=409, detail={"error":"out of stock", "refund":request.cash_amount})

        precond = {"_id":"INR"}
        if combo:
            precond.setdefault("$and", [])
            for d in combo:
                precond["$and"].append({"denoms":{"$elemMatch":{"value":d["value"], "count":{"$gte":d["count"]}}}})

        inc_updates={}
        array_filters=[]

        for idx, d in enumerate(combo):
            var = f"d{idx}"
            inc_updates[f"denoms.$[{var}].count"]=-int(d["count"])
            array_filters.append({f"{var}.value":d["value"]})

        try:
            res = db.cash_drawer.find_one_and_update(
                precond,
                {"$inc": inc_updates} if inc_updates else {},
                array_filters=array_filters if array_filters else None,
                return_document=ReturnDocument.AFTER,
            )
        except Exception as e:
            db.products.update_one({"_id": request.snack_id}, {"$inc":{"qty": quantity}})
            raise HTTPException(status_code=500, detail="internal db error")

        if res:
            if updated_product.get("qty", 0) == 0:
                db.products.update_one({"_id": request.snack_id, "qty": 0}, {"$set": {"status": "Sold Out"}})

            tx = {
                "snack_id":request.snack_id,
                "unit_price": unit_price,
                "quantity": quantity,
                "price": total_price,
                "cash_in":request.cash_amount,
                "change":combo,
                "status":"SUCCESS",
                "ts":time.time()
            }
            db.transactions.insert_one(tx)
            resp = {"snack_id":request.snack_id, "price":total_price, "change":combo, "remaining_qty":updated_product.get("qty", 0)}
            if Idempotency_Key:
                save_idempotent_result(db, Idempotency_Key, resp)
            return resp

        db.products.update_one({"_id":request.snack_id}, {"$inc":{"qty": quantity}})

        time.sleep(0.03 + random.random()*0.03)
        drawer = trino_get_drawer("INR")
        if not drawer:
            raise HTTPException(status_code=500, detail="cash drawer not initialize")
        denoms = drawer["denoms"]

    raise HTTPException(status_code=409, detail={"error":"change not available after retries", "refund":request.cash_amount})