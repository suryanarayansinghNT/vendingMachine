# app/routers/products.py
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas import Product
from app.trino_client import get_trino_conn
from trino.exceptions import TrinoQueryError, TrinoUserError

router = APIRouter(prefix="/products", tags=["products"])

ALLOWED_STATUS = {"Available", "Sold Out"}

@router.get("", response_model=List[Product])
def list_products(
    limit: int = Query(25, ge=1, le=100),
    cursor: int | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
):
    
    if status is not None and status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail=f"invalid status (allowed: {ALLOWED_STATUS})")

    if category is not None:
        if not isinstance(category, str) or len(category) > 100:
            raise HTTPException(status_code=400, detail="invalid category")

    where_clauses: list[str] = []
    params: list = []

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    if category:
        where_clauses.append("category = ?")
        params.append(category)

    if cursor is not None:
        try:
            cursor = int(cursor)
        except Exception:
            raise HTTPException(status_code=400, detail="cursor must be an integer")
        where_clauses.append('"_id" > ?')
        params.append(cursor)

    sql = (
        'select "_id", name, price, qty, status, category, description '
        "from mongodb.app.products"
    )
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += f' ORDER BY "_id" ASC LIMIT {int(limit)}'

    try:
        with get_trino_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
    except TrinoQueryError as e:
        print("TrinoQueryError:", str(e))
        raise HTTPException(status_code=502, detail="Query failed in Trino")
    except Exception as e:
        print("Unexpected error while querying Trino:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

    result = [
        {
            "id": int(r[0]),
            "name": r[1],
            "price": int(r[2]),
            "qty": int(r[3]),
            "status": r[4],
            "category": r[5],
            "description": r[6],
        }
        for r in rows
    ]

    return result
