import os, csv, json, re
from dotenv import load_dotenv
from phi.agent import Agent
from phi.model.groq import Groq

load_dotenv()

agent = Agent(
    name="ProductGenerator",
    model=Groq(
        id="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    ),
    markdown=False,
)

def extract_json(text: str) -> str:
    m = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL) \
        or re.search(r'(\[.*?\])', text, re.DOTALL)
    return m.group(1) if m else text

def generate_batch(batch_size: int, start_id: int) -> list:
    prompt = f"""
Generate {batch_size} unique e-commerce product names.
Mix electronics, fashion, and groceries.
Include a few similar variants and typo-style names.

Return ONLY valid JSON:
[
  {{"product_id": {start_id}, "product_name": "Product Name"}}
]

Product IDs must be sequential starting from {start_id}.
Product names should be realistic and 5–12 words.
"""

    try:
        data = json.loads(extract_json(agent.run(prompt).content))
        if not isinstance(data, list):
            raise ValueError
        for p in data:
            if "product_id" not in p or "product_name" not in p:
                raise ValueError
        return data

    except json.JSONDecodeError:
        return [
            {"product_id": start_id + i, "product_name": f"Product {start_id + i}"}
            for i in range(batch_size)
        ]
    except Exception:
        return []

def generate_products(total=500, batch=50) -> list:
    products = []
    for i in range(0, total, batch):
        products += generate_batch(min(batch, total - i), i + 1)
    return products

def save_csv(data, file="products.csv"):
    with open(file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["product_id", "product_name"])
        w.writeheader()
        w.writerows(data)

if __name__ == "__main__":
    products = generate_products()
    save_csv(products)
    print(f"{len(products)} products created")
