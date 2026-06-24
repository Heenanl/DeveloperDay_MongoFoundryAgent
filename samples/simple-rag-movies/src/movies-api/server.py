"""
Movies Tool API — plain Flask server for Azure Container Apps.
Exposes: /api/embed, /api/mongo/vector-search, /api/mongo/find, /api/mongo/aggregate, /api/health
"""
import json
import logging
import os
import urllib.request
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util

logging.basicConfig(level=logging.INFO)

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "sample_mflix")
VECTOR_INDEX = os.environ.get("VECTOR_INDEX", "vector_index")
VECTOR_PATH = os.environ.get("VECTOR_PATH", "plot_embedding")

app = Flask(__name__)

_mongo_client = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        if not MONGODB_CONNECTION_STRING:
            raise ValueError("MONGODB_CONNECTION_STRING is not configured")
        _mongo_client = MongoClient(MONGODB_CONNECTION_STRING)
    return _mongo_client


def call_azure_openai_embedding(text: str) -> list:
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version=2024-06-01"
    data = json.dumps({"input": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"api-key": AZURE_OPENAI_API_KEY, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["data"][0]["embedding"]


@app.route("/api/embed", methods=["POST"])
def generate_embedding():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON"}), 400
    text = body.get("text")
    if not text:
        return jsonify({"error": "Missing required field: text"}), 400
    try:
        embedding = call_azure_openai_embedding(text)
        return jsonify({"embedding": embedding, "dimensions": len(embedding), "model": EMBEDDING_MODEL})
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mongo/vector-search", methods=["POST"])
def mongo_vector_search():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON"}), 400
    query_embedding = body.get("queryEmbedding")
    if not isinstance(query_embedding, list) or not query_embedding:
        return jsonify({"error": "Missing required field: queryEmbedding"}), 400
    collection_name = body.get("collection", "embedded_movies")
    limit = int(body.get("limit", 10))
    num_candidates = int(body.get("numCandidates", max(limit * 10, 100)))
    project = body.get("project", {"title": 1, "plot": 1, "year": 1, "genres": 1})
    try:
        col = get_mongo_client()[MONGODB_DATABASE][collection_name]
        pipeline = [
            {"$vectorSearch": {
                "index": VECTOR_INDEX, "path": VECTOR_PATH,
                "queryVector": query_embedding, "numCandidates": num_candidates, "limit": limit
            }},
            {"$project": {**project, "score": {"$meta": "vectorSearchScore"}, "_id": 0}}
        ]
        results = json.loads(json_util.dumps(list(col.aggregate(pipeline))))
        return jsonify({"results": results})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Vector search failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mongo/find", methods=["POST"])
def mongo_find():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON"}), 400
    collection_name = body.get("collection", "movies")
    query_filter = body.get("filter", {})
    projection = body.get("projection", {"_id": 0})
    sort = body.get("sort")
    limit = int(body.get("limit", 20))
    try:
        col = get_mongo_client()[MONGODB_DATABASE][collection_name]
        cursor = col.find(query_filter, projection)
        if isinstance(sort, dict) and sort:
            cursor = cursor.sort(list(sort.items()))
        docs = json.loads(json_util.dumps(list(cursor.limit(limit))))
        return jsonify({"results": docs})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Find failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mongo/aggregate", methods=["POST"])
def mongo_aggregate():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON"}), 400
    collection_name = body.get("collection", "movies")
    pipeline = body.get("pipeline")
    if not isinstance(pipeline, list) or not pipeline:
        return jsonify({"error": "Missing required field: pipeline"}), 400
    try:
        col = get_mongo_client()[MONGODB_DATABASE][collection_name]
        docs = json.loads(json_util.dumps(list(col.aggregate(pipeline))))
        return jsonify({"results": docs})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Aggregate failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model": EMBEDDING_MODEL,
        "openai_configured": bool(AZURE_OPENAI_ENDPOINT),
        "mongodb_configured": bool(MONGODB_CONNECTION_STRING),
        "mongodb_database": MONGODB_DATABASE,
        "vector_index": VECTOR_INDEX
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
