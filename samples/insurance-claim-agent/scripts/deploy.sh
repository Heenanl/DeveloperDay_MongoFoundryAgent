#!/bin/bash
# Quick deployment script for Insurance Claim Agent

set -e

# Resolve sample root directory (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SAMPLE_DIR"

echo "=== Insurance Claim Agent Deployment ==="
echo "Running from: $SAMPLE_DIR"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"; exit 1; }
command -v func >/dev/null 2>&1 || { echo "Azure Functions Core Tools required. Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"; exit 1; }
command -v python >/dev/null 2>&1 || { echo "Python 3.11+ is required. Install from https://python.org"; exit 1; }

# Prompt for required values
read -p "Resource Group Name [insurance-claim-agent-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-insurance-claim-agent-rg}

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

read -p "Image Model Name [gpt-4o]: " IMAGE_MODEL
IMAGE_MODEL=${IMAGE_MODEL:-gpt-4o}

read -sp "Voyage AI API Key: " VOYAGE_API_KEY
echo ""
if [ -z "$VOYAGE_API_KEY" ]; then
    echo "Voyage AI API key is required"
    exit 1
fi

read -p "Voyage Model Name [voyage-3]: " VOYAGE_MODEL
VOYAGE_MODEL=${VOYAGE_MODEL:-voyage-3}

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
echo "=== Deploying Image Analysis Function ==="
IMAGE_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/image-analysis-function/main.bicep \
    --parameters azureOpenAIEndpoint="$OPENAI_ENDPOINT" \
                 azureOpenAIKey="$OPENAI_KEY" \
                 imageModel="$IMAGE_MODEL" \
    --query "properties.outputs" -o json)

IMAGE_FUNC_NAME=$(echo $IMAGE_OUTPUT | jq -r '.functionAppName.value')
IMAGE_URL=$(echo $IMAGE_OUTPUT | jq -r '.functionAppUrl.value')
echo "Image Analysis Function URL: $IMAGE_URL"

echo ""
echo "=== Deploying Image Analysis Function Code ==="
cd src/image-analysis-function
func azure functionapp publish $IMAGE_FUNC_NAME
cd ../..

echo ""
echo "=== Deploying Embedding Function ==="
EMBED_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/embedding-function/main.bicep \
    --parameters voyageApiKey="$VOYAGE_API_KEY" \
                 voyageModel="$VOYAGE_MODEL" \
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
echo "MCP Server URL:              $MCP_URL"
echo "Image Analysis Function URL: $IMAGE_URL"
echo "Embedding Function URL:      $EMBED_URL"
echo ""
echo "Next Steps:"
echo "1. Go to https://ai.azure.com"
echo "2. Create the Filing Agent:"
echo "   - Model: gpt-4o"
echo "   - Add OpenAPI tool (Image Analyzer): $IMAGE_URL"
echo "   - Add MCP tool (MongoDB): $MCP_URL"
echo "   - Instructions: docs/agent-instructions-filing.md"
echo "3. Create the Assessment Agent:"
echo "   - Model: gpt-4.1"
echo "   - Add OpenAPI tool (Embedding Generator): $EMBED_URL"
echo "   - Add MCP tool (MongoDB): $MCP_URL"
echo "   - Instructions: docs/agent-instructions-assessment.md"
echo ""
