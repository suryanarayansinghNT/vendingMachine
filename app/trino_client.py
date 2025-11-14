import os
from trino.dbapi import connect as trino_connect

def get_trino_conn():
    host=os.getenv("TRINO_HOST", "localhost")
    port=int(os.getenv("TINO_PORT", "8080"))
    user=os.getenv("TRINO_user", "surya")
    return trino_connect(host=host, port=port, user=user)