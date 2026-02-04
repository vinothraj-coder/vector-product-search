import csv
import json
import pickle
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 2),
    lowercase=True,
    stop_words="english"
)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vijay@123",
        database="product_search"
    )

def load_products(file="products.csv"):
    with open(file, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def generate_embeddings(products):
    names = [p["product_name"] for p in products]
    vectors = vectorizer.fit_transform(names).toarray()

    for p, v in zip(products, vectors):
        p["vector"] = v.tolist()

    return products

def insert_to_db(products):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM products_vectors")
    cur.executemany(
        "INSERT INTO products_vectors (product_id, product_name, vector) VALUES (%s, %s, %s)",
        [(int(p["product_id"]), p["product_name"], json.dumps(p["vector"])) for p in products]
    )

    conn.commit()
    cur.close()
    conn.close()

def main():
    products = load_products()
    products = generate_embeddings(products)
    insert_to_db(products)
    print(f"{len(products)} products indexed successfully")

if __name__ == "__main__":
    main()
