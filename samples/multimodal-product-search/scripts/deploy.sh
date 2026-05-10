#!/bin/bash
# Deployment script for Multimodal Product Search Sample

set -e

# Resolve sample root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SAMPLE_DIR"

echo "=== Multimodal Product Search - Deployment ==="
echo "Running from: $SAMPLE_DIR"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"; exit 1; }
command -v func >/dev/null 2>&1 || { echo "Azure Functions Core Tools required. Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"; exit 1; }

# Prompt for required values
read -p "Resource Group Name [multimodal-search-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-multimodal-search-rg}

read -p "Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "MongoDB Connection String: " MDB_CONNECTION_STRING
if [ -z "$MDB_CONNECTION_STRING" ]; then
    echo "MongoDB connection string is required"
    exit 1
fi

read -sp "Voyage AI API Key (starts with pa-): " VOYAGE_API_KEY
echo ""
if [ -z "$VOYAGE_API_KEY" ]; then
    echo "Voyage AI API key is required"
    exit 1
fi

read -p "Voyage Model [voyage-multimodal-3]: " VOYAGE_MODEL
VOYAGE_MODEL=${VOYAGE_MODEL:-voyage-multimodal-3}

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
echo "=== Deploying Embedding Function ==="
FUNC_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file deploy/embedding-function/main.bicep \
    --parameters voyageApiKey="$VOYAGE_API_KEY" \
                 voyageModel="$VOYAGE_MODEL" \
    --query "properties.outputs" -o json)

FUNC_NAME=$(echo $FUNC_OUTPUT | jq -r '.functionAppName.value')
EMBED_URL=$(echo $FUNC_OUTPUT | jq -r '.functionAppUrl.value')

echo "Embedding Function URL: $EMBED_URL"

echo ""
echo "=== Deploying Function Code ==="
cd src/embedding-function
func azure functionapp publish $FUNC_NAME
cd ../..

echo ""
echo "=== Loading Sample Product Data ==="
echo "Installing data loader dependencies..."
pip install -r src/data-loader/requirements.txt --quiet
python src/data-loader/load_products.py \
    --connection-string "$MDB_CONNECTION_STRING" \
    --voyage-api-key "$VOYAGE_API_KEY"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "MCP Server URL: $MCP_URL"
echo "Embedding API URL: $EMBED_URL"
echo ""
echo "Next Steps:"
echo "1. Go to https://ai.azure.com"
echo "2. Create a new agent"
echo "3. Add OpenAPI tool with URL: $EMBED_URL"
echo "4. Add MCP tool with URL: $MCP_URL"
echo "5. Copy instructions from docs/agent-instructions.md"
echo ""
