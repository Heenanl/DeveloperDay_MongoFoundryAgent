"""Data Loader for SwiftShip Logistics Voice Customer Support Sample.

Loads sample orders and policies into MongoDB Atlas.
Generates embeddings for policy documents using Azure OpenAI text-embedding-3-small.

Usage:
    python load_data.py --connection-string "mongodb+srv://..." \
                        --azure-openai-endpoint "https://..." \
                        --azure-openai-key "your-key"
"""
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

import pymongo


EMBEDDING_MODEL = "text-embedding-3-small"
DATABASE_NAME = "swiftship"


def load_json_file(filepath: str) -> list[dict]:
    """Load and parse a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_embedding(text: str, endpoint: str, api_key: str) -> list[float]:
    """Generate embedding vector for text using Azure OpenAI."""
    url = f"{endpoint}/openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version=2024-06-01"
    data = json.dumps({"input": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


def load_orders(db, orders_file: str) -> int:
    """Load sample orders into the orders collection."""
    orders = load_json_file(orders_file)
    collection = db["orders"]

    # Drop existing data for clean reload
    collection.drop()
    collection.insert_many(orders)

    print(f"  Loaded {len(orders)} orders into '{DATABASE_NAME}.orders'")
    return len(orders)


def load_policies(db, policies_file: str, endpoint: str, api_key: str) -> int:
    """Load sample policies with embeddings into the policies collection."""
    policies = load_json_file(policies_file)
    collection = db["policies"]

    # Drop existing data for clean reload
    collection.drop()

    for i, policy in enumerate(policies):
        print(f"  Generating embedding for policy: {policy['title']} ({i + 1}/{len(policies)})")
        embedding = generate_embedding(policy["content"], endpoint, api_key)
        policy["embedding"] = embedding
        policy["embedding_model"] = EMBEDDING_MODEL
        policy["loaded_at"] = datetime.now(timezone.utc).isoformat()

    collection.insert_many(policies)

    print(f"  Loaded {len(policies)} policies with embeddings into '{DATABASE_NAME}.policies'")
    return len(policies)


def create_vector_search_index(db):
    """Create a vector search index on the policies collection."""
    collection = db["policies"]
    index_name = "vector_index"

    # Check if the index already exists
    existing_indexes = list(collection.list_search_indexes())
    for idx in existing_indexes:
        if idx.get("name") == index_name:
            print(f"  Vector search index '{index_name}' already exists, skipping creation")
            return

    index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            },
            {
                "type": "filter",
                "path": "category"
            }
        ]
    }

    try:
        collection.create_search_index(
            model=pymongo.operations.SearchIndexModel(
                definition=index_definition,
                name=index_name,
                type="vectorSearch"
            )
        )
        print(f"  Created vector search index '{index_name}' on '{DATABASE_NAME}.policies'")
        print("  Note: Index may take a few minutes to become active on Atlas")
    except Exception as e:
        print(f"  Warning: Could not create vector search index: {e}")
        print("  You may need to create the index manually in the Atlas UI")


def main():
    parser = argparse.ArgumentParser(
        description="Load sample data into MongoDB Atlas for SwiftShip voice support demo"
    )
    parser.add_argument(
        "--connection-string",
        required=True,
        help="MongoDB Atlas connection string (mongodb+srv://...)"
    )
    parser.add_argument(
        "--azure-openai-endpoint",
        required=True,
        help="Azure OpenAI endpoint URL (https://your-resource.openai.azure.com)"
    )
    parser.add_argument(
        "--azure-openai-key",
        required=True,
        help="Azure OpenAI API key"
    )
    parser.add_argument(
        "--database",
        default=DATABASE_NAME,
        help=f"MongoDB database name (default: {DATABASE_NAME})"
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    orders_file = os.path.join(script_dir, "sample_orders.json")
    policies_file = os.path.join(script_dir, "sample_policies.json")

    # Verify data files exist
    for filepath in [orders_file, policies_file]:
        if not os.path.exists(filepath):
            print(f"Error: Data file not found: {filepath}")
            sys.exit(1)

    print(f"Connecting to MongoDB Atlas...")
    client = pymongo.MongoClient(args.connection_string)
    db = client[args.database]

    # Verify connectivity
    try:
        client.admin.command("ping")
        print("  Connected successfully")
    except Exception as e:
        print(f"Error: Could not connect to MongoDB: {e}")
        sys.exit(1)

    print(f"\nLoading data into database '{args.database}'...")
    print("-" * 50)

    # Load orders
    print("\n[1/3] Loading sample orders...")
    order_count = load_orders(db, orders_file)

    # Load policies with embeddings
    print("\n[2/3] Loading sample policies with embeddings...")
    policy_count = load_policies(db, policies_file, args.azure_openai_endpoint, args.azure_openai_key)

    # Create vector search index
    print("\n[3/3] Creating vector search index...")
    create_vector_search_index(db)

    # Summary
    print("\n" + "=" * 50)
    print("Data loading complete!")
    print(f"  Database:    {args.database}")
    print(f"  Orders:      {order_count} documents in 'orders' collection")
    print(f"  Policies:    {policy_count} documents in 'policies' collection")
    print(f"  Embeddings:  {EMBEDDING_MODEL} (1536 dimensions)")
    print(f"  Index:       vector_index on 'policies.embedding'")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    main()
