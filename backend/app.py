from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        database=os.environ.get("DB_NAME", "inventory"),
        user=os.environ.get("DB_USER", "admin"),
        password=os.environ.get("DB_PASSWORD", "secret")
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            quantity INTEGER DEFAULT 0,
            price DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'In Stock'
        )
    """)
    # Seed data
    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO items (name, category, quantity, price, status) VALUES (%s,%s,%s,%s,%s)",
            [
                ("Laptop Dell XPS", "Electronics", 15, 1299.99, "In Stock"),
                ("Office Chair", "Furniture", 8, 349.50, "In Stock"),
                ("USB-C Hub", "Accessories", 0, 49.99, "Out of Stock"),
                ("Standing Desk", "Furniture", 3, 599.00, "Low Stock"),
                ("Mechanical Keyboard", "Electronics", 22, 129.99, "In Stock"),
            ]
        )
    conn.commit()
    cur.close()
    conn.close()

@app.route("/api/items", methods=["GET"])
def get_items():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, category, quantity, price, status FROM items ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {"id": r[0], "name": r[1], "category": r[2],
         "quantity": r[3], "price": float(r[4]), "status": r[5]}
        for r in rows
    ])

@app.route("/api/items", methods=["POST"])
def add_item():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (name, category, quantity, price, status) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (data["name"], data["category"], data["quantity"], data["price"], data.get("status", "In Stock"))
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": new_id, **data}), 201

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Deleted"})

if __name__ == "__main__":
    import time
    time.sleep(3)  # Wait for DB to be ready
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
