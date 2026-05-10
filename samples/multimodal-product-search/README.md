# Multimodal Product Search — Visual Search Agent with Azure AI Foundry

[← Back to all samples](../../README.md)

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fvpriyanshi%2Fmongodb-foundry-agent%2Fmain%2Fsamples%2Fmultimodal-product-search%2Fdeploy%2Fazuredeploy.json)

Build an AI agent that performs **multimodal product search** — find products by text description, image similarity, or both — using Azure AI Foundry, MongoDB Atlas, and Voyage AI embeddings.

## What You'll Build

A hosted AI agent in Azure AI Foundry that can:
- **Text Search**: "red leather handbag" → semantic product matching
- **Image Search**: Upload a product photo → find visually similar items
- **Hybrid Search**: "shoes like this but in blue" → image + text combined
- **Filtered Search**: "dresses under $50" → vector search + field filters
- **Aggregations**: Average price by category, brand breakdowns

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure AI Foundry                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Hosted Agent (gpt-4.1)                      │  │
│  └──────────┬───────────────────┬────────────────────────────┘  │
│             │                   │                               │
│    ┌────────▼────────┐  ┌──────▼────────┐                      │
│    │  OpenAPI Tool   │  │   MCP Tool    │                      │
│    │ (Multimodal     │  │  (MongoDB)    │                      │
│    │  Embeddings)    │  │               │                      │
│    └────────┬────────┘  └──────┬────────┘                      │
└─────────────┼──────────────────┼────────────────────────────────┘
              │                  │
     ┌────────▼────────┐  ┌─────▼──────────────┐
     │ Azure Function  │  │  MongoDB MCP       │
     │ (Embedding API) │  │  Server (ACA)      │
     │ text / image /  │  └─────┬──────────────┘
     │ both → vector   │        │
     └────────┬────────┘  ┌─────▼──────────────┐
              │           │  MongoDB Atlas      │
     ┌────────▼────────┐  │  product_catalog DB │
     │   Voyage AI     │  │  products collection│
     │  voyage-        │  │  (vector index)     │
     │  multimodal-3   │  └────────────────────┘
     └─────────────────┘
```

## Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas)
- [Voyage AI API Key](https://www.voyageai.com/) (keys start with `pa-`)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- [Python 3.11+](https://python.org)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/vpriyanshi/mongodb-foundry-agent.git
cd mongodb-foundry-agent/samples/multimodal-product-search
```

### 2. Deploy the MongoDB MCP Server

```bash
az login

az group create --name multimodal-search-rg --location eastus

az deployment group create \
  --resource-group multimodal-search-rg \
  --template-file deploy/mcp-server/main.bicep \
  --parameters mdbConnectionString="<YOUR_MONGODB_CONNECTION_STRING>"
```

Note the MCP Server URL from the output.

### 3. Deploy the Embedding Function

```bash
# Deploy infrastructure
az deployment group create \
  --resource-group multimodal-search-rg \
  --template-file deploy/embedding-function/main.bicep \
  --parameters voyageApiKey="<YOUR_VOYAGE_API_KEY>"

# Deploy function code
cd src/embedding-function
func azure functionapp publish <FUNCTION_APP_NAME>
cd ../..
```

Note the Function URL from the output.

### 4. Load Sample Product Data

```bash
# Install dependencies
pip install -r src/data-loader/requirements.txt

# Load 50 sample products with embeddings
python src/data-loader/load_products.py \
  --connection-string "<YOUR_MONGODB_CONNECTION_STRING>" \
  --voyage-api-key "<YOUR_VOYAGE_API_KEY>"
```

This creates the `product_catalog` database with a `products` collection and vector search index.

### 5. Create the Agent in Azure AI Foundry

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project → **Agents** → **+ New Agent**
3. Configure:
   - **Name**: `product-search-agent`
   - **Model**: `gpt-4.1`
   - **Instructions**: Copy from [agent-instructions.md](./docs/agent-instructions.md)

4. Add **OpenAPI Tool** (Multimodal Embedding Generator):
   - Name: `MultimodalEmbeddingGenerator`
   - Description: `Generates text, image, or combined embeddings for product search`
   - Authentication: `Anonymous`
   - Schema: Copy from [openapi-schema.json](./docs/openapi-schema.json) (update the server URL)

5. Add **MCP Tool** (MongoDB):
   - Name: `MongoDB`
   - URL: `https://<your-mcp-server>.azurecontainerapps.io/mcp`

6. Click **Create**

### 6. Test Your Agent

Try these queries in the Foundry playground:
- "Find me a comfortable everyday bag"
- "Show me leather shoes under $150"
- "Elegant evening accessories"

See [sample-queries.md](./sample-queries.md) for more examples.

## MongoDB Atlas Setup

### Create a Cluster

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a cluster (M0 free tier works)

### Create Vector Search Index

If the data loader doesn't create the index automatically, create it manually:

1. Go to **Atlas Search** → **Create Search Index**
2. Select **JSON Editor**
3. Choose database: `product_catalog`, collection: `products`
4. Index name: `product_vector_index`
5. Paste this definition:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

> **Note**: `voyage-multimodal-3` produces 1024-dimensional embeddings. Adjust `numDimensions` if using a different model.

6. Click **Create Search Index**

### Whitelist Azure IPs

1. Get the Container App's outbound IP:
   ```bash
   az containerapp show --name mongo-mcp-server --resource-group multimodal-search-rg \
     --query "properties.outboundIpAddresses" -o tsv
   ```
2. Go to MongoDB Atlas → **Network Access** → **Add IP Address**
3. Add the IP from step 1 (or use `0.0.0.0/0` for testing)

## Sample Structure

```
multimodal-product-search/
├── README.md                              # This file
├── sample-queries.md                      # Example queries to test
├── src/
│   ├── embedding-function/                # Azure Function for multimodal embeddings
│   │   ├── function_app.py                # Voyage AI voyage-multimodal-3 integration
│   │   ├── host.json
│   │   ├── local.settings.json.template
│   │   └── requirements.txt
│   └── data-loader/                       # Product data loader
│       ├── load_products.py               # Loads products + generates embeddings
│       ├── sample_products.json           # 50 synthetic products
│       └── requirements.txt
├── deploy/
│   ├── azuredeploy.json                   # One-click ARM deployment
│   ├── mcp-server/
│   │   └── main.bicep                     # MongoDB MCP Server deployment
│   └── embedding-function/
│       └── main.bicep                     # Embedding Function deployment
├── docs/
│   ├── agent-instructions.md              # Agent system prompt
│   └── openapi-schema.json                # OpenAPI spec (multimodal input)
└── scripts/
    ├── deploy.sh                          # Bash deployment script
    └── deploy.ps1                         # PowerShell deployment script
```

## Configuration Options

### Embedding Function

| Setting | Description | Default |
|---------|-------------|---------|
| `VOYAGE_API_KEY` | Voyage AI API key (starts with `pa-`) | Required |
| `VOYAGE_MODEL` | Voyage AI model name | `voyage-multimodal-3` |

### MCP Server

| Setting | Description | Default |
|---------|-------------|---------|
| `MDB_MCP_CONNECTION_STRING` | MongoDB connection string | Required |
| `MDB_MCP_READ_ONLY` | Restrict to read operations | `true` |
| `MDB_MCP_HTTP_PORT` | HTTP port | `8080` |

## Product Dataset

The sample includes 50 synthetic products across 5 categories:

| Category | Count | Examples |
|----------|-------|----------|
| Bags | 9 | Tote, crossbody, clutch, backpack, messenger |
| Shoes | 10 | Running, boots, sneakers, sandals, loafers |
| Dresses | 10 | Wrap, cocktail, midi, maxi, denim, tops |
| Accessories | 9 | Scarves, belts, watches, jewelry, hats |
| Outerwear | 9 | Coats, jackets, blazers, fleece, knitwear |

Brands: UrbanCraft, DayTrip, LuxeNoir, ActiveGear, SunCoast, Heritage, BloomStyle, StrideMax, EasyStep, AutumnWalk, ShadeHouse, TimeCraft, ArtisanGems

## Cost Estimate

| Component | Tier | Estimated Cost |
|-----------|------|----------------|
| Azure Function | Consumption | ~$0 (free tier) |
| Container App (MCP) | Consumption | ~$0-5/month |
| Voyage AI | Pay-per-token | ~$0.06/1M tokens |
| MongoDB Atlas | M0 | Free |
| **Total** | | **~$0-10/month** |

## Troubleshooting

### "Embedding generation failed"
- Verify `VOYAGE_API_KEY` is set and starts with `pa-`
- Check the Voyage AI model name matches `VOYAGE_MODEL`
- Ensure your Voyage AI account has API credits

### "MongoDB connection failed"
- Verify the connection string includes username and password
- Check MongoDB Atlas network access allows Azure IPs
- Ensure the MCP server container is running

### "Vector search returned no results"
- Verify `product_vector_index` exists on the `products` collection
- Check the index status is "Active" in Atlas
- Ensure embeddings were generated during data loading (check loader output)
- Confirm `numDimensions` matches the model output (1024 for voyage-multimodal-3)

### "Image embedding not working"
- Ensure the image is base64-encoded (not a URL)
- Strip the `data:image/...;base64,` prefix before sending
- Check image size is under 2MB

## Resources

- [Voyage AI Documentation](https://docs.voyageai.com/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
