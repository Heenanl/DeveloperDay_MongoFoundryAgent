"""Azure Function for Embedding Generation.

Simple REST API to generate text embeddings using Azure OpenAI.
Designed to be used as an OpenAPI tool in Azure AI Foundry agents.
"""
import azure.functions as func
import json
import logging
import os
import urllib.request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "sample_mflix")
VECTOR_INDEX = os.environ.get("VECTOR_INDEX", "vector_index")
VECTOR_PATH = os.environ.get("VECTOR_PATH", "plot_embedding")

_mongo_client = None


def get_mongo_client() -> MongoClient:
    """Create and cache a MongoDB client."""
    global _mongo_client
    if _mongo_client is None:
        if not MONGODB_CONNECTION_STRING:
            raise ValueError("MONGODB_CONNECTION_STRING is not configured")
        _mongo_client = MongoClient(MONGODB_CONNECTION_STRING)
    return _mongo_client


def json_response(payload: dict | list, status_code: int = 200) -> func.HttpResponse:
    """Return a JSON HTTP response."""
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        mimetype="application/json"
    )


def parse_body(req: func.HttpRequest) -> dict | None:
    """Parse JSON request body, returning None when invalid."""
    try:
        return req.get_json()
    except ValueError:
        return None


def call_azure_openai_embedding(text: str) -> list[float]:
    """Generate embedding vector for text using Azure OpenAI."""
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_MODEL}/embeddings?api-version=2024-06-01"
    data = json.dumps({"input": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


@app.route(route="embed", methods=["POST"])
def generate_embedding(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generate embedding vector for text.
    
    Request body: {"text": "your text here"}
    Response: {"embedding": [0.1, 0.2, ...], "dimensions": 1536, "model": "..."}
    """
    logging.info("Embedding request received")
    
    body = parse_body(req)
    if body is None:
        return json_response({"error": "Invalid JSON in request body"}, 400)
    
    text = body.get("text")
    if not text:
        return json_response({"error": "Missing required field: text"}, 400)
    
    try:
        embedding = call_azure_openai_embedding(text)
        logging.info(f"Generated embedding for: {text[:50]}... (dims: {len(embedding)})")
        
        return json_response({
            "embedding": embedding,
            "dimensions": len(embedding),
            "model": EMBEDDING_MODEL
        })
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        return json_response({"error": f"Embedding generation failed: {str(e)}"}, 500)


@app.route(route="mongo/vector-search", methods=["POST"])
def mongo_vector_search(req: func.HttpRequest) -> func.HttpResponse:
    """
    Perform MongoDB Atlas vector search.

    Request body:
    {
      "queryEmbedding": [0.1, 0.2, ...],
      "collection": "embedded_movies",
      "limit": 10,
      "numCandidates": 100,
      "project": {"title": 1, "plot": 1, "year": 1, "genres": 1}
    }
    """
    body = parse_body(req)
    if body is None:
        return json_response({"error": "Invalid JSON in request body"}, 400)

    query_embedding = body.get("queryEmbedding")
    if not isinstance(query_embedding, list) or not query_embedding:
        return json_response({"error": "Missing required field: queryEmbedding (number array)"}, 400)

    collection_name = body.get("collection", "embedded_movies")
    limit = int(body.get("limit", 10))
    num_candidates = int(body.get("numCandidates", max(limit * 10, 100)))
    project = body.get("project", {"title": 1, "plot": 1, "year": 1, "genres": 1})

    try:
        db = get_mongo_client()[MONGODB_DATABASE]
        collection = db[collection_name]

        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX,
                    "path": VECTOR_PATH,
                    "queryVector": query_embedding,
                    "numCandidates": num_candidates,
                    "limit": limit
                }
            },
            {
                "$project": {
                    **project,
                    "score": {"$meta": "vectorSearchScore"},
                    "_id": 0
                }
            }
        ]

        results = list(collection.aggregate(pipeline))
        return json_response({"results": json.loads(json_util.dumps(results))})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Vector search failed: {e}")
        return json_response({"error": f"Vector search failed: {str(e)}"}, 500)


@app.route(route="mongo/find", methods=["POST"])
def mongo_find(req: func.HttpRequest) -> func.HttpResponse:
    """
    Run MongoDB find query.

    Request body:
    {
      "collection": "movies",
      "filter": {"year": 1994},
      "projection": {"title": 1, "year": 1, "_id": 0},
      "sort": {"imdb.rating": -1},
      "limit": 20
    }
    """
    body = parse_body(req)
    if body is None:
        return json_response({"error": "Invalid JSON in request body"}, 400)

    collection_name = body.get("collection", "movies")
    query_filter = body.get("filter", {})
    projection = body.get("projection", {"_id": 0})
    sort = body.get("sort")
    limit = int(body.get("limit", 20))

    try:
        db = get_mongo_client()[MONGODB_DATABASE]
        collection = db[collection_name]
        cursor = collection.find(query_filter, projection)
        if isinstance(sort, dict) and sort:
            cursor = cursor.sort(list(sort.items()))
        docs = list(cursor.limit(limit))
        return json_response({"results": json.loads(json_util.dumps(docs))})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Find query failed: {e}")
        return json_response({"error": f"Find query failed: {str(e)}"}, 500)


@app.route(route="mongo/aggregate", methods=["POST"])
def mongo_aggregate(req: func.HttpRequest) -> func.HttpResponse:
    """
    Run MongoDB aggregate pipeline.

    Request body:
    {
      "collection": "movies",
      "pipeline": [{"$match": {"genres": "Sci-Fi"}}, {"$sort": {"imdb.rating": -1}}, {"$limit": 10}]
    }
    """
    body = parse_body(req)
    if body is None:
        return json_response({"error": "Invalid JSON in request body"}, 400)

    collection_name = body.get("collection", "movies")
    pipeline = body.get("pipeline")
    if not isinstance(pipeline, list) or not pipeline:
        return json_response({"error": "Missing required field: pipeline (array)"}, 400)

    try:
        db = get_mongo_client()[MONGODB_DATABASE]
        collection = db[collection_name]
        docs = list(collection.aggregate(pipeline))
        return json_response({"results": json.loads(json_util.dumps(docs))})
    except (ValueError, PyMongoError) as e:
        logging.error(f"Aggregate query failed: {e}")
        return json_response({"error": f"Aggregate query failed: {str(e)}"}, 500)


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return json_response({
        "status": "healthy",
        "model": EMBEDDING_MODEL,
        "openai_endpoint_configured": bool(AZURE_OPENAI_ENDPOINT),
        "mongodb_configured": bool(MONGODB_CONNECTION_STRING),
        "mongodb_database": MONGODB_DATABASE,
        "vector_index": VECTOR_INDEX
    })
