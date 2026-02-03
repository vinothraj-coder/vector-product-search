import json, pickle, os
import mysql.connector
import numpy as np

_vectorizer = None


def load_vectorizer():
    global _vectorizer
    if _vectorizer is None:
        with open("tfidf_vectorizer.pkl", "rb") as f:
            _vectorizer = pickle.load(f)
    return _vectorizer


def connect_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Vijay@123"),
        database=os.getenv("DB_NAME", "product_search"),
    )


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else np.dot(a, b) / (na * nb)


def search_products(query):
    vec = load_vectorizer()
    qv = vec.transform([query]).toarray()[0]

    conn = connect_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT product_name, vector FROM products_vectors")

    results = [
        {"name": r["product_name"], "sim": cosine_similarity(qv, json.loads(r["vector"]))}
        for r in cur.fetchall()
        if cosine_similarity(qv, json.loads(r["vector"])) > 0
    ]

    cur.close()
    conn.close()

    if not results:
        return []

    results.sort(key=lambda x: x["sim"], reverse=True)
    top = results[0]["sim"]
    words = query.lower().split()

    if len(words) >= 2:
        strict = [
            r for r in results
            if all(w in r["name"].lower() for w in words)
        ]
        filtered = strict or [
            r for r in results if r["sim"] >= max(0.55, top * 0.85)
        ]
    else:
        filtered = [
            r for r in results if r["sim"] >= max(0.30, top * 0.40)
        ]

    return [r["name"] for r in filtered[:5]]


def lambda_handler(event, context):
    try:
        body = event.get("body", event)
        if isinstance(body, str):
            body = json.loads(body)

        query = body.get("query", "").strip()
        if not query:
            return {"statusCode": 400, "body": json.dumps({"error": "Query required"})}

        products = search_products(query)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "query": query,
                "products": products,
                "count": len(products)
            })
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


if __name__ == "__main__":
    while True:
        try:
            q = input("\nSearch: ").strip()
            if q.lower() in {"q", "quit", "exit"}:
                break
            if not q:
                continue

            res = json.loads(lambda_handler({"query": q}, None)["body"])
            if res.get("products"):
                print(f"\nFound {res['count']} products:\n")
                for i, p in enumerate(res["products"], 1):
                    print(f"{i}. {p}")
            else:
                print("\nNo products found.")
        except KeyboardInterrupt:
            break
