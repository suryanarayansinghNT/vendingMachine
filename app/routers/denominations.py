from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import CashDrawer, Denomination
from app.trino_client import get_trino_conn
from trino.exceptions import TrinoQueryError

router = APIRouter(prefix="/denominations", tags=["denominations"])

@router.get("", response_model=CashDrawer)
def get_denominations(currency: str="INR"):
    if not isinstance(currency, str) or len(currency) > 10:
        raise HTTPException(status_code=400)
    
    sql = "select _id, denoms from mongodb.app.cash_drawer where _id = ?"

    try:
        with get_trino_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, [currency])
            rows=cur.fetchall()
    except TrinoQueryError as e:
        print("TrinoQueryError:", str(e))
        raise HTTPException(status_code=500, detail="query failed in trino")
    except Exception as e:
        print("errorr querying trino:", str(e))
        raise HTTPException(status_code=500)
    
    if not rows:
        raise HTTPException(status_code=404, detail="cash not found")
    
    _id = rows[0][0]
    denoms_raw=rows[0][1] or []

    denoms: List[dict]=[]
    
    for d in denoms_raw:
        if isinstance(d, dict):
            val=d.get("value")
            cnt=d.get("count")
        elif isinstance(d, (list, tuple)) and len(d) >= 2:
            val, cnt = d[0], d[1]
        else:
            val=getattr(d, "value", None)
            cnt=getattr(d, "count", None)
        denoms.append({"value":int(val), "count":int(cnt)})
    
    return {"currency": _id, "denoms": denoms}