# Vending Machine Simulation — FastAPI + Trino + MongoDB

A production-style **Vending Machine API** built with:

- FastAPI (Python backend)  
- Trino (SQL query engine on MongoDB)  
- MongoDB (data store for products, drawer, transactions)  
- Minikube + Helm (Trino + optional Mongo deployments)

The backend supports:
- Product listing with pagination & filtering  
- Purchasing items with multi-quantity support  
- Change calculation based on available denominations  
- Automatic Sold-Out marking  
- Idempotency for safe retrying  
- Reads through Trino, writes through MongoDB  
- Transaction logging & compensation logic  

---

# Architecture

    Client
      ↓
    FastAPI Backend
      ↓ (READ)
    Trino → MongoDB (datasource)
      ↓ (WRITE)
    MongoDB (direct writes)

  Trino handles all read operations  
  MongoDB handles all writes & atomic updates  

---

# Setup Instructions

## 1️ Start Minikube
    minikube start

## 2️ Install Trino and map it to localhost
    minikube start

## 3 Configure Trino Mongo Catalog  
Edit `trino-catalogs-values.yaml`:

    catalogs:
      mongodb: |
        connector.name=mongodb
        mongodb.connection-url=mongodb://<HOST/IP>:27017

Apply config:

    helm upgrade my-trino trino/trino -n trino -f trino-catalogs-values.yaml
    kubectl -n trino rollout restart deployment my-trino-trino
    minikube kubectl -- -n trino port-forward svc/my-trino-trino 8080:8080

## 5️ Start FastAPI locally

    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

---

# Project Structure

    app/
    ├── routers/
    │   ├── products.py
    │   ├── purchase.py
    │   ├── status.py
    │   └── denominations.py
    ├── schemas.py
    ├── trino_client.py
    ├── db.py
    └── main.py
    seed.py

---

# Sample Seed Data

### Product Document
    {
      "_id": 101,
      "name": "Chips",
      "price": 25,
      "qty": 10,
      "status": "Available",
      "category": "Snacks",
      "description": "Classic salted potato chips"
    }

### Cash Drawer Document
    {
      "_id": "INR",
      "denoms": [
        {"value": 20, "count": 10},
        {"value": 10, "count": 15},
        {"value": 5, "count": 20},
        {"value": 1, "count": 50}
      ]
    }

---

# API Endpoints

## 1️ GET /products

Returns available products using Trino.

Supports:
- limit  
- cursor  
- category filter  
- Automatically filters items with qty == 0 or status != "Available"

Example:
    GET /products?limit=5&category=Snacks

Sample Response:
    [
      {
        "id": 101,
        "name": "Chips",
        "price": 25,
        "qty": 10,
        "status": "Available",
        "category": "Snacks",
        "description": "Classic salted potato chips"
      }
    ]

---

## 2️ POST /purchase

Handles a purchase with:
- Quantity support  
- Change calculation  
- Atomic qty decrement  
- Atomic drawer decrement  
- Compensation rollback  
- Idempotency  
- Auto Sold-Out  
- Transaction logging  

Example Request:
    {
      "snack_id": 101,
      "cash_amount": 50,
      "quantity": 1
    }

Example Response:
    {
      "snack_id": 101,
      "price": 25,
      "change": [
        {"value": 20, "count": 1},
        {"value": 5, "count": 1}
      ],
      "remaining_qty": 9
    }

---

## 3️ GET /status/{snack_id}

Fetches live product status via Trino.

Example:
    GET /status/101

Example Response:
    {
      "id": 101,
      "name": "Chips",
      "price": 25,
      "qty": 9,
      "status": "Available",
      "category": "Snacks",
      "description": "potato chips"
    }

---

## 4️ GET /denominations
 
Fetches available denominations.

Example:
    GET /denominations

Example Response:
    {
      "currency": "INR",
      "denoms": [
        {"value":20,"count":10},
        {"value":10,"count":15},
        {"value":5,"count":20}
      ]
    }

---

# Idempotency

Use header:
    Idempotency-Key: <uuid>

- Server returns saved response if repeated  
- Prevents duplicate purchases  
- Stored in Mongo `idempotency` collection  

---

# Change Calculation (Backtracking)

- Calculates valid change combinations  
- Uses available denom counts  
- More accurate than greedy  

---

# Reliability & Safety

| Feature | Description |
|--------|-------------|
| Atomic updates | Mongo find_one_and_update |
| Compensation | Rolls back qty on failure |
| Retry logic | Handles race conditions |
| Idempotency | Prevents double-charging |
| Auto Sold-Out | qty == 0 triggers status update |
| SQL safety | Trino query validation |
| Error handling | For both Mongo + Trino | 

---

# Conclusion

A complete vending machine backend featuring:

- FastAPI  
- Trino SQL reads  
- MongoDB atomic writes  
- Change-making logic  
- Idempotency  
- Multi-quantity purchases  
- Safe, production-style workflows  

Fully ready to extend, deploy, or integrate!
