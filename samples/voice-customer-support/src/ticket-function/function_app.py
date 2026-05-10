"""Azure Function for Support Ticket CRUD Operations.

REST API for creating and retrieving customer support tickets.
Connects to MongoDB Atlas for persistent storage.
"""
import azure.functions as func
import json
import logging
import os
from datetime import datetime, timezone

import pymongo

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# MongoDB configuration
MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "swiftship")

VALID_PRIORITIES = {"high", "medium", "low"}


def get_mongo_client():
    """Create and return a MongoDB client."""
    return pymongo.MongoClient(MONGODB_CONNECTION_STRING)


def generate_ticket_id(collection) -> str:
    """Generate a ticket ID in format TKT-YYYYMMDD-NNN."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"TKT-{today}-"

    # Count existing tickets for today
    today_count = collection.count_documents({"_id": {"$regex": f"^{prefix}"}})
    next_number = today_count + 1

    return f"{prefix}{next_number:03d}"


@app.route(route="ticket", methods=["POST"])
def create_ticket(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create a new support ticket.

    Request body: {
        "order_id": "ORD-2024-1001",
        "customer_name": "Jane Smith",
        "issue_type": "damaged_item",
        "description": "Item arrived with broken screen",
        "priority": "high"
    }
    Response: {"ticket_id": "TKT-20260510-001", "status": "open", "created_at": "..."}
    """
    logging.info("Create ticket request received")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json"
        )

    # Validate required fields
    required_fields = ["order_id", "customer_name", "issue_type", "description", "priority"]
    missing = [f for f in required_fields if not body.get(f)]
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing required fields: {', '.join(missing)}"}),
            status_code=400,
            mimetype="application/json"
        )

    priority = body["priority"].lower()
    if priority not in VALID_PRIORITIES:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        client = get_mongo_client()
        db = client[MONGODB_DATABASE]
        collection = db["tickets"]

        now = datetime.now(timezone.utc)
        ticket_id = generate_ticket_id(collection)

        ticket = {
            "_id": ticket_id,
            "order_id": body["order_id"],
            "customer_name": body["customer_name"],
            "issue_type": body["issue_type"],
            "description": body["description"],
            "priority": priority,
            "status": "open",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "resolution": None,
            "notes": []
        }

        collection.insert_one(ticket)
        logging.info(f"Created ticket: {ticket_id}")

        return func.HttpResponse(
            json.dumps({
                "ticket_id": ticket_id,
                "status": "open",
                "created_at": now.isoformat()
            }),
            status_code=201,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Failed to create ticket: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to create ticket: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
    finally:
        client.close()


@app.route(route="ticket/{ticket_id}", methods=["GET"])
def get_ticket(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get a support ticket by ID.

    Response: Full ticket document.
    """
    ticket_id = req.route_params.get("ticket_id")
    logging.info(f"Get ticket request: {ticket_id}")

    if not ticket_id:
        return func.HttpResponse(
            json.dumps({"error": "Ticket ID is required"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        client = get_mongo_client()
        db = client[MONGODB_DATABASE]
        collection = db["tickets"]

        ticket = collection.find_one({"_id": ticket_id})
        if not ticket:
            return func.HttpResponse(
                json.dumps({"error": f"Ticket not found: {ticket_id}"}),
                status_code=404,
                mimetype="application/json"
            )

        return func.HttpResponse(
            json.dumps(ticket, default=str),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Failed to get ticket: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get ticket: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
    finally:
        client.close()
