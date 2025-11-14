import trino

def main():
    try:
        # Connect to Trino running in Minikube (forwarded to localhost:8080)
        conn = trino.dbapi.connect(
            host="localhost",
            port=8080,
            user="surya",   # or any username you use
        )
        cur = conn.cursor()

        # List all catalogs (like 'system', 'mongodb', etc.)
        cur.execute("SHOW CATALOGS")
        catalogs = [row[0] for row in cur.fetchall()]
        print("✅ Connected to Trino!")
        print("📦 Available catalogs:", catalogs)

    except Exception as e:
        print("❌ Trino connection error:", type(e).__name__, e)


if __name__ == "__main__":
    main()
