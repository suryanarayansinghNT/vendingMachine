# test_trino_fetch.py
import trino

def main():
    try:
        # Use trino.dbapi.connect (DB-API style)
        conn = trino.dbapi.connect(host="localhost", port=8080, user="surya")
        cur = conn.cursor()
        cur.execute("SELECT _id, name, price, qty FROM mongodb.app.products LIMIT 15")
        rows = cur.fetchall()
        print("ROWS:", rows)
    except Exception as e:
        print("ERROR:", type(e).__name__, e)

if __name__ == "__main__":
    main()
