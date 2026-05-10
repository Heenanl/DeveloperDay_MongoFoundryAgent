"""Azure Function for Multimodal Embedding Generation.

REST API to generate text, image, or combined text+image embeddings
using Voyage AI's voyage-multimodal-3 model.
Designed to be used as an OpenAPI tool in Azure AI Foundry agents.
"""
import azure.functions as func
import json
import logging
import os
import urllib.request

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Voyage AI configuration
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY")
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-multimodal-3")


def call_voyage_embedding(inputs: list[dict]) -> list[float]:
    """Generate embedding vector using Voyage AI multimodal API.

    Args:
        inputs: List of input objects, each with 'type' ('text' or 'image')
                and 'data' (text string or base64-encoded image).
    Returns:
        Embedding vector as list of floats.
    """
    data = json.dumps({
        "model": VOYAGE_MODEL,
        "input": [inputs],
        "input_type": "query"
    }).encode("utf-8")

    req = urllib.request.Request(
        VOYAGE_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {VOYAGE_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


@app.route(route="embed-multimodal", methods=["POST"])
def generate_multimodal_embedding(req: func.HttpRequest) -> func.HttpResponse:
    """
    Generate embedding vector for text, image, or both.

    Request body (all fields optional, but at least one required):
      {"text": "your text here", "image": "base64-encoded-image"}

    Response:
      {"embedding": [...], "dimensions": N, "model": "...", "input_type": "text|image|multimodal"}
    """
    logging.info("Multimodal embedding request received")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json"
        )

    text = body.get("text")
    image = body.get("image")

    if not text and not image:
        return func.HttpResponse(
            json.dumps({"error": "At least one of 'text' or 'image' is required"}),
            status_code=400,
            mimetype="application/json"
        )

    # Build Voyage AI input array
    inputs = []
    if text:
        inputs.append({"type": "text", "data": text})
    if image:
        # Strip data URL prefix if present
        if image.startswith("data:"):
            image = image.split(",", 1)[1]
        inputs.append({"type": "image", "data": image})

    # Determine input type for response
    if text and image:
        input_type = "multimodal"
    elif text:
        input_type = "text"
    else:
        input_type = "image"

    try:
        embedding = call_voyage_embedding(inputs)
        logging.info(
            f"Generated {input_type} embedding "
            f"(dims: {len(embedding)}, text: {text[:50] if text else 'none'}...)"
        )

        return func.HttpResponse(
            json.dumps({
                "embedding": embedding,
                "dimensions": len(embedding),
                "model": VOYAGE_MODEL,
                "input_type": input_type
            }),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Embedding generation failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "model": VOYAGE_MODEL,
            "api_key_configured": bool(VOYAGE_API_KEY)
        }),
        mimetype="application/json"
    )
