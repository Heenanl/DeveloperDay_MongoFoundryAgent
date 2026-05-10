import azure.functions as func
import json
import logging
import os
import urllib.request

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _get_embedding(api_key: str, model: str, text: str) -> dict:
    """Call Voyage AI embeddings API for a text input."""
    url = "https://api.voyageai.com/v1/embeddings"

    body = json.dumps(
        {
            "input": [{"type": "text", "data": text}],
            "model": model,
        }
    ).encode("utf-8")

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
        return json.loads(resp.read().decode("utf-8"))


@app.route(route="embed", methods=["POST"])
def embed(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a text embedding via Voyage AI."""
    logging.info("embed invoked")

    api_key = os.environ.get("VOYAGE_API_KEY", "")
    model = os.environ.get("VOYAGE_MODEL", "voyage-3")

    if not api_key:
        return func.HttpResponse(
            json.dumps({"error": "VOYAGE_API_KEY must be set"}),
            status_code=500,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json",
        )

    text = body.get("text", "")
    if not text:
        return func.HttpResponse(
            json.dumps({"error": "Missing 'text' field"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        result = _get_embedding(api_key, model, text)
        embedding = result["data"][0]["embedding"]

        return func.HttpResponse(
            json.dumps(
                {
                    "embedding": embedding,
                    "dimensions": len(embedding),
                    "model": model,
                }
            ),
            mimetype="application/json",
        )
    except Exception as exc:
        logging.exception("Error calling Voyage AI")
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=502,
            mimetype="application/json",
        )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health-check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "embedding-function"}),
        mimetype="application/json",
    )
