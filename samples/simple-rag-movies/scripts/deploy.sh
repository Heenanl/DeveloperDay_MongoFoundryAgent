#!/bin/bash
# Quick deployment script for MongoDB Vector Search Agent

set -e

# Resolve sample root directory (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SAMPLE_DIR"

echo "=== MongoDB Vector Search Agent Deployment ==="
echo "Running from: $SAMPLE_DIR"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"; exit 1; }

# Prompt for required values
read -p "Resource Group Name [mongodb-agent-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-mongodb-agent-rg}

read -p "Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "MongoDB Connection String: " MDB_CONNECTION_STRING
if [ -z "$MDB_CONNECTION_STRING" ]; then
    echo "MongoDB connection string is required"
    exit 1
fi

read -p "Azure AI Foundry resource endpoint (e.g., https://myfoundry.openai.azure.com): " OPENAI_ENDPOINT
if [ -z "$OPENAI_ENDPOINT" ]; then
    echo "Foundry resource endpoint is required"
    exit 1
fi

read -p "Azure AI Foundry resource key: " OPENAI_KEY
if [ -z "$OPENAI_KEY" ]; then
    echo "Foundry resource key is required"
    exit 1
fi

read -p "Embedding Model Name [text-embedding-ada-002]: " EMBEDDING_MODEL
EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-ada-002}

MOVIES_API_NAME="movies-tool-api"

echo ""
echo "=== Creating Resource Group ==="
az group create --name $RESOURCE_GROUP --location $LOCATION

echo ""
echo "=== Deploying MongoDB MCP Server ==="
MCP_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/mcp-server/main.bicep \
    --parameters mdbConnectionString="$MDB_CONNECTION_STRING" \
    --query "properties.outputs" -o json)

MCP_URL=$(echo $MCP_OUTPUT | jq -r '.mcpServerUrl.value')
echo "MCP Server URL: $MCP_URL"

echo ""
echo "=== Deploying Movies Tool API (Container Apps, build from source) ==="
cd src/movies-api
az containerapp up \
    --name "$MOVIES_API_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --source . \
    --target-port 8080 \
    --ingress external \
    --env-vars \
        AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
        EMBEDDING_MODEL="$EMBEDDING_MODEL" \
        MONGODB_CONNECTION_STRING="$MDB_CONNECTION_STRING"
cd ../..

API_FQDN=$(az containerapp show --name "$MOVIES_API_NAME" --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" -o tsv)
API_BASE_URL="https://$API_FQDN/api"
echo "Movies Tool API: $API_BASE_URL"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "MCP Server URL  : $MCP_URL"
echo "Movies Tool API : $API_BASE_URL"
echo ""
echo "Next Steps:"
echo "1. Go to https://ai.azure.com"
echo "2. Create a new agent"
echo "3. Add OpenAPI tool (EmbeddingGenerator) with server URL: $API_BASE_URL"
echo "4. Add MCP tool (MongoDB) with URL: $MCP_URL"
echo "5. Copy instructions from docs/agent-instructions.md"
echo ""
