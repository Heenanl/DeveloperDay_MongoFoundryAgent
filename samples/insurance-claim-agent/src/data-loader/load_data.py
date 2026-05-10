"""
Data loader for the Insurance Claim Agent sample.

Loads sample claims and policy documents into MongoDB Atlas,
generates embeddings for policy documents via Voyage AI,
and creates a vector search index.

Usage:
    python load_data.py --connection-string "mongodb+srv://..." --voyage-api-key "pa-..."
"""

import argparse
import json
import os
import sys
import urllib.request

from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

DATABASE_NAME = "insurance_claims"
CLAIMS_COLLECTION = "claims"
POLICIES_COLLECTION = "policy_documents"
VECTOR_INDEX_NAME = "policy_vector_index"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename: str) -> list:
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_embedding(api_key: str, model: str, text: str) -> list[float]:
    """Call Voyage AI to get an embedding vector for the given text."""
    url = "https://api.voyageai.com/v1/embeddings"
    body = json.dumps({
        "input": [{"type": "text", "data": text}],
        "model": model,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["data"][0]["embedding"]


def load_claims(db) -> int:
    """Load sample claims into the claims collection."""
    claims = load_json("sample_claims.json")
    collection = db[CLAIMS_COLLECTION]
    collection.drop()
    collection.insert_many(claims)
    return len(claims)


def load_policies(db, voyage_api_key: str, voyage_model: str) -> int:
    """Load policy documents with embeddings into the policy_documents collection."""
    policies = load_json("sample_policies.json")
    collection = db[POLICIES_COLLECTION]
    collection.drop()

    for i, policy in enumerate(policies):
        text_to_embed = f"{policy['title']}\n\n{policy['content']}"
        print(f"  Generating embedding for policy {i + 1}/{len(policies)}: {policy['title']}")
        embedding = get_embedding(voyage_api_key, voyage_model, text_to_embed)
        policy["embedding"] = embedding

    collection.insert_many(policies)
    return len(policies)


def create_vector_index(db):
    """Create a vector search index on the policy_documents collection."""
    collection = db[POLICIES_COLLECTION]

    # Check if the index already exists
    existing_indexes = list(collection.list_search_indexes())
    for idx in existing_indexes:
        if idx.get("name") == VECTOR_INDEX_NAME:
            print(f"  Vector search index '{VECTOR_INDEX_NAME}' already exists, dropping...")
            collection.drop_search_index(VECTOR_INDEX_NAME)
            break

    print(f"  Creating vector search index '{VECTOR_INDEX_NAME}'...")
    index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1024,
                "similarity": "cosine",
            }
        ]
    }
    search_index = SearchIndexModel(
        definition=index_definition,
        name=VECTOR_INDEX_NAME,
        type="vectorSearch",
    )
    collection.create_search_index(model=search_index)


def main():
    parser = argparse.ArgumentParser(description="Load insurance sample data into MongoDB Atlas")
    parser.add_argument("--connection-string", required=True, help="MongoDB Atlas connection string")
    parser.add_argument("--voyage-api-key", required=True, help="Voyage AI API key")
    parser.add_argument("--voyage-model", default="voyage-3", help="Voyage embedding model (default: voyage-3)")
    args = parser.parse_args()

    print("=" * 60)
    print("Insurance Claim Agent - Data Loader")
    print("=" * 60)

    print("\nConnecting to MongoDB Atlas...")
    client = MongoClient(args.connection_string)
    db = client[DATABASE_NAME]

    # Verify connection
    client.admin.command("ping")
    print("  Connected successfully.")

    # Step 1: Load claims
    print("\nStep 1: Loading sample claims...")
    claims_count = load_claims(db)
    print(f"  Loaded {claims_count} claims into {DATABASE_NAME}.{CLAIMS_COLLECTION}")

    # Step 2: Load policies with embeddings
    print(f"\nStep 2: Loading policy documents with embeddings (model: {args.voyage_model})...")
    policies_count = load_policies(db, args.voyage_api_key, args.voyage_model)
    print(f"  Loaded {policies_count} policies into {DATABASE_NAME}.{POLICIES_COLLECTION}")

    # Step 3: Create vector search index
    print(f"\nStep 3: Creating vector search index...")
    create_vector_index(db)
    print(f"  Index '{VECTOR_INDEX_NAME}' created (may take a few minutes to build).")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Database:        {DATABASE_NAME}")
    print(f"  Claims loaded:   {claims_count} -> {CLAIMS_COLLECTION}")
    print(f"  Policies loaded: {policies_count} -> {POLICIES_COLLECTION}")
    print(f"  Vector index:    {VECTOR_INDEX_NAME} on {POLICIES_COLLECTION}.embedding")
    print(f"  Embedding model: {args.voyage_model}")
    print("\nDone!")

    client.close()


if __name__ == "__main__":
    main()
