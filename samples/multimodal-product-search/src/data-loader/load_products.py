"""Load sample product data into MongoDB Atlas with multimodal embeddings.

Usage:
    pip install -r requirements.txt
    python load_products.py \
        --connection-string "mongodb+srv://..." \
        --voyage-api-key "pa-..." \
        --embedding-function-url "https://your-func.azurewebsites.net/api/embed-multimodal"
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

try:
    from pymongo import MongoClient
    from pymongo.operations import SearchIndexModel
except ImportError:
    print("pymongo is required. Install with: pip install pymongo[srv]")
    sys.exit(1)

DATABASE_NAME = "product_catalog"
COLLECTION_NAME = "products"
VECTOR_INDEX_NAME = "product_vector_index"
SAMPLE_DATA_FILE = Path(__file__).parent / "sample_products.json"


def generate_embedding(text: str, embedding_url: str) -> list[float]:
    """Generate text embedding via the Azure Function."""
    data = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        embedding_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        return result["embedding"]


def generate_embedding_voyage_direct(text: str, voyage_api_key: str) -> list[float]:
    """Generate text embedding directly via Voyage AI API."""
    data = json.dumps({
        "model": "voyage-multimodal-3",
        "input": [[{"type": "text", "data": text}]],
        "input_type": "document"
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.voyageai.com/v1/embeddings",
        data=data,
        headers={
            "Authorization": f"Bearer {voyage_api_key}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


def load_products(
    connection_string: str,
    voyage_api_key: str = None,
    embedding_url: str = None
):
    """Load sample products into MongoDB with embeddings."""
    if not voyage_api_key and not embedding_url:
        print("Error: Provide either --voyage-api-key or --embedding-function-url")
        sys.exit(1)

    # Load sample data
    with open(SAMPLE_DATA_FILE) as f:
        products = json.load(f)

    print(f"Loaded {len(products)} products from sample data")

    # Connect to MongoDB
    client = MongoClient(connection_string)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Drop existing data
    existing = collection.count_documents({})
    if existing > 0:
        print(f"Dropping {existing} existing documents...")
        collection.delete_many({})

    # Generate embeddings and insert
    print("Generating embeddings (this may take a minute)...")
    for i, product in enumerate(products):
        # Create combined text for embedding
        embed_text = f"{product['name']}. {product['description']}. " \
                     f"Category: {product['category']}. Color: {product['color']}. " \
                     f"Material: {product['material']}."

        try:
            if embedding_url:
                product["embedding"] = generate_embedding(embed_text, embedding_url)
            else:
                product["embedding"] = generate_embedding_voyage_direct(
                    embed_text, voyage_api_key
                )
            print(f"  [{i+1}/{len(products)}] {product['name']} ✓")
        except Exception as e:
            print(f"  [{i+1}/{len(products)}] {product['name']} ✗ Error: {e}")
            continue

        # Rate limiting
        time.sleep(0.2)

    # Insert into MongoDB
    products_with_embeddings = [p for p in products if "embedding" in p]
    result = collection.insert_many(products_with_embeddings)
    print(f"\nInserted {len(result.inserted_ids)} products into "
          f"{DATABASE_NAME}.{COLLECTION_NAME}")

    # Create vector search index
    print(f"\nCreating vector search index '{VECTOR_INDEX_NAME}'...")
    try:
        dims = len(products_with_embeddings[0]["embedding"])
        index_definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": dims,
                    "similarity": "cosine"
                }
            ]
        }
        search_index = SearchIndexModel(
            definition=index_definition,
            name=VECTOR_INDEX_NAME,
            type="vectorSearch"
        )
        collection.create_search_index(model=search_index)
        print(f"Vector index '{VECTOR_INDEX_NAME}' created ({dims} dimensions)")
        print("Note: Index may take a few minutes to become active in Atlas.")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"Vector index '{VECTOR_INDEX_NAME}' already exists")
        else:
            print(f"Could not create index programmatically: {e}")
            print("Create it manually in Atlas (see README for index definition).")

    client.close()
    print("\nDone! Your product catalog is ready.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load sample product data into MongoDB Atlas"
    )
    parser.add_argument(
        "--connection-string",
        required=True,
        help="MongoDB Atlas connection string"
    )
    parser.add_argument(
        "--voyage-api-key",
        help="Voyage AI API key (starts with 'pa-'). "
             "Used to generate embeddings directly."
    )
    parser.add_argument(
        "--embedding-function-url",
        help="URL of the deployed Azure Function embedding endpoint. "
             "Alternative to direct Voyage API calls."
    )
    args = parser.parse_args()
    load_products(args.connection_string, args.voyage_api_key, args.embedding_function_url)
