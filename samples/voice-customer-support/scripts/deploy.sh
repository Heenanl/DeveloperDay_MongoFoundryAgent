#!/bin/bash
# Quick deployment script for Voice Customer Support Agent

set -e

# Resolve sample root directory (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SAMPLE_DIR"

echo "=== Voice Customer Support Agent Deployment ==="
echo "Running from: $SAMPLE_DIR"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"; exit 1; }
command -v func >/dev/null 2>&1 || { echo "Azure Functions Core Tools required. Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"; exit 1; }

# Prompt for required values
read -p "Resource Group Name [voice-support-agent-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-voice-support-agent-rg}

read -p "Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -sp "MongoDB Connection String: " MDB_CONNECTION_STRING
echo ""
if [ -z "$MDB_CONNECTION_STRING" ]; then
    echo "MongoDB connection string is required"
    exit 1
fi

read -p "Azure OpenAI Endpoint (e.g., https://myresource.openai.azure.com): " OPENAI_ENDPOINT
if [ -z "$OPENAI_ENDPOINT" ]; then
    echo "Azure OpenAI endpoint is required"
    exit 1
fi

read -sp "Azure OpenAI API Key: " OPENAI_KEY
echo ""
if [ -z "$OPENAI_KEY" ]; then
    echo "Azure OpenAI API key is required"
    exit 1
fi

read -p "Embedding Model Name [text-embedding-3-small]: " EMBEDDING_MODEL
EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-3-small}

echo ""
echo "=== Creating Resource Group ==="
az group create --name $RESOURCE_GROUP --location $LOCATION

echo ""
echo "=== Deploying MongoDB MCP Server ==="
MCP_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/mcp-server/main.bicep \
    --parameters mdbConnectionString="$MDB_CONNECTION_STRING" \
                 readOnlyMode=false \
    --query "properties.outputs" -o json)

MCP_URL=$(echo $MCP_OUTPUT | jq -r '.mcpServerUrl.value')
echo "MCP Server URL: $MCP_URL"

echo ""
echo "=== Deploying Embedding Function ==="
EMBED_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/embedding-function/main.bicep \
    --parameters azureOpenAIEndpoint="$OPENAI_ENDPOINT" \
                 azureOpenAIKey="$OPENAI_KEY" \
                 embeddingModel="$EMBEDDING_MODEL" \
    --query "properties.outputs" -o json)

EMBED_FUNC_NAME=$(echo $EMBED_OUTPUT | jq -r '.functionAppName.value')
EMBED_URL=$(echo $EMBED_OUTPUT | jq -r '.functionAppUrl.value')
echo "Embedding Function URL: $EMBED_URL"

echo ""
echo "=== Deploying Embedding Function Code ==="
cd src/embedding-function
func azure functionapp publish $EMBED_FUNC_NAME
cd ../..

echo ""
echo "=== Deploying Ticket Function ==="
TICKET_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/ticket-function/main.bicep \
    --parameters mongodbConnectionString="$MDB_CONNECTION_STRING" \
    --query "properties.outputs" -o json)

TICKET_FUNC_NAME=$(echo $TICKET_OUTPUT | jq -r '.functionAppName.value')
TICKET_URL=$(echo $TICKET_OUTPUT | jq -r '.functionAppUrl.value')
echo "Ticket Function URL: $TICKET_URL"

echo ""
echo "=== Deploying Ticket Function Code ==="
cd src/ticket-function
func azure functionapp publish $TICKET_FUNC_NAME
cd ../..

echo ""
echo "=== Loading Sample Data ==="
cd src/data-loader
pip install -r requirements.txt
python load_data.py
cd ../..

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "MCP Server URL:          $MCP_URL"
echo "Embedding API URL:       $EMBED_URL"
echo "Ticket Function URL:     $TICKET_URL"
echo ""
echo "Next Steps:"
echo "1. Go to https://ai.azure.com"
echo "2. Create a new agent"
echo "3. Add MCP tool with URL: $MCP_URL"
echo "4. Add OpenAPI tool for embeddings: $EMBED_URL"
echo "5. Add OpenAPI tool for tickets: $TICKET_URL"
echo "6. Copy instructions from docs/agent-instructions.md"
echo ""
