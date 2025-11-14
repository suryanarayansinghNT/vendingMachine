from fastapi import APIRouter, HTTPException
from app.trino_client import get_trino_conn
from trino.exceptions import TrinoQueryError

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/{snack_id}")
def get_status(snack_id: int):

    sql = (
        'select "_id", name, price, qty, status, category, description '
        "from mongodb.app.products "
        f'where "_id" = {int(snack_id)}'
    )

    try:
        with get_trino_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
    except TrinoQueryError as e:
        print("trino query error:", str(e))
        raise HTTPException(status_code=502,detail="query failed trino")
    except Exception as e:
        print("Unexpected error:", str(e))
        raise HTTPException(status_code=500,detail="internal error")

    if not rows:
        raise HTTPException(status_code=404,detail="product not found")

    r = rows[0]
    item = {
        "id": int(r[0]),
        "name": r[1],
        "price": int(r[2]),
        "qty": int(r[3]),
        "status": r[4],
        "category": r[5],
        "description": r[6],
    }
    return item