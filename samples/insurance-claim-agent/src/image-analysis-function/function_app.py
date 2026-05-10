import azure.functions as func
import json
import logging
import os
import re
import urllib.request

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

SYSTEM_PROMPT = (
    "You are an auto insurance damage assessor. Analyze this vehicle accident photo. "
    "Describe: 1) Visible damage, 2) Affected vehicle parts, 3) Estimated severity "
    "(minor/moderate/severe/total_loss), 4) Safety concerns. Be factual and concise."
)

SEVERITY_LEVELS = {"minor", "moderate", "severe", "total_loss"}


def _extract_severity(description: str) -> str:
    """Parse severity from the model's description text."""
    text_lower = description.lower()
    for level in ("total_loss", "severe", "moderate", "minor"):
        if level.replace("_", " ") in text_lower or level in text_lower:
            return level
    return "unknown"


def _call_openai(endpoint: str, api_key: str, model: str, image_b64: str, prompt: str) -> dict:
    """Call Azure OpenAI chat/completions with a base64 image."""
    url = f"{endpoint.rstrip('/')}/openai/deployments/{model}/chat/completions?api-version=2024-06-01"

    user_content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
        },
    ]
    if prompt:
        user_content.insert(0, {"type": "text", "text": prompt})

    body = json.dumps(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 1024,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


@app.route(route="analyze-image", methods=["POST"])
def analyze_image(req: func.HttpRequest) -> func.HttpResponse:
    """Accept a base64-encoded accident photo and return a damage description."""
    logging.info("analyze-image invoked")

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
    model = os.environ.get("IMAGE_MODEL", "gpt-4o")

    if not endpoint or not api_key:
        return func.HttpResponse(
            json.dumps({"error": "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set"}),
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

    image_b64 = body.get("image", "")
    if not image_b64:
        return func.HttpResponse(
            json.dumps({"error": "Missing 'image' field (base64-encoded image)"}),
            status_code=400,
            mimetype="application/json",
        )

    prompt = body.get("prompt", "")

    try:
        result = _call_openai(endpoint, api_key, model, image_b64, prompt)
        description = result["choices"][0]["message"]["content"]
        severity = _extract_severity(description)

        return func.HttpResponse(
            json.dumps(
                {
                    "description": description,
                    "model": model,
                    "severity_estimate": severity,
                }
            ),
            mimetype="application/json",
        )
    except Exception as exc:
        logging.exception("Error calling Azure OpenAI")
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=502,
            mimetype="application/json",
        )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health-check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "image-analysis-function"}),
        mimetype="application/json",
    )
