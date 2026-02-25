# MongoDB Vector Search Agent with Azure AI Foundry

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FYOUR_ORG%2Fmongodb-foundry-agent%2Fmain%2Fdeploy%2Fazuredeploy.json)

Build intelligent agents that perform semantic search over your MongoDB data using Azure AI Foundry and the MongoDB MCP Server.

![Architecture Diagram](./docs/architecture.png)

## What You'll Build

A hosted AI agent in Azure AI Foundry that can:
- **Semantic Search**: Find documents by meaning, not just keywords ("movies about hope and redemption")
- **Direct Queries**: Filter by specific fields (year, genre, cast)
- **Aggregations**: Get statistics, top results, counts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure AI Foundry                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Hosted Agent                           │  │
│  │                    (gpt-4.1)                              │  │
│  └───────────────┬─────────────────────┬─────────────────────┘  │
│                  │                     │                        │
│         ┌───────▼───────┐     ┌───────▼───────┐                │
│         │  OpenAPI Tool │     │   MCP Tool    │                │
│         │  (Embeddings) │     │  (MongoDB)    │                │
│         └───────┬───────┘     └───────┬───────┘                │
└─────────────────┼─────────────────────┼─────────────────────────┘
                  │                     │
         ┌───────▼───────┐     ┌───────▼───────┐
         │ Azure Function│     │  MongoDB MCP  │
         │ (Embedding API)│     │    Server    │
         └───────┬───────┘     └───────┬───────┘
                  │                     │
         ┌───────▼───────┐     ┌───────▼───────┐
         │  Azure OpenAI │     │ MongoDB Atlas │
         │  (ada-002)    │     │ (Vector Index)│
         └───────────────┘     └───────────────┘
```

## Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas) with:
  - `sample_mflix` sample database loaded
  - Vector search index created (see [Setup](#mongodb-atlas-setup))
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_ORG/mongodb-foundry-agent.git
cd mongodb-foundry-agent
```

### 2. Deploy the MongoDB MCP Server

```bash
# Login to Azure
az login

# Create resource group
az group create --name mongodb-agent-rg --location eastus

# Deploy MCP Server (Azure Container Apps)
az deployment group create \
  --resource-group mongodb-agent-rg \
  --template-file deploy/mcp-server/main.bicep \
  --parameters mdbConnectionString="<YOUR_MONGODB_CONNECTION_STRING>"
```

Note the MCP Server URL from the output: `https://<app-name>.<region>.azurecontainerapps.io/mcp`

### 3. Deploy the Embedding Function

```bash
# Create storage account
az storage account create \
  --name embeddingfuncstore \
  --resource-group mongodb-agent-rg \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --name embedding-api-func \
  --resource-group mongodb-agent-rg \
  --storage-account embeddingfuncstore \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux

# Configure Azure OpenAI credentials
az functionapp config appsettings set \
  --name embedding-api-func \
  --resource-group mongodb-agent-rg \
  --settings \
    AZURE_OPENAI_ENDPOINT="<YOUR_AZURE_OPENAI_ENDPOINT>" \
    AZURE_OPENAI_API_KEY="<YOUR_AZURE_OPENAI_KEY>" \
    EMBEDDING_MODEL="text-embedding-ada-002"

# Deploy function code
cd src/embedding-function
func azure functionapp publish embedding-api-func
```

Note the Function URL: `https://embedding-api-func.azurewebsites.net/api/embed`

### 4. Create the Agent in Azure AI Foundry

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project
3. Navigate to **Agents** → **+ New Agent**
4. Configure:
   - **Name**: `mongodb-search-agent`
   - **Model**: `gpt-4.1` (or your deployed model)
   - **Instructions**: Copy from [agent-instructions.md](./docs/agent-instructions.md)

5. Add **OpenAPI Tool** (Embedding Generator):
   - Name: `EmbeddingGenerator`
   - Description: `Generates embeddings for semantic search`
   - Authentication: `Anonymous`
   - Schema: Copy from [openapi-schema.json](./docs/openapi-schema.json) (update the server URL)

6. Add **MCP Tool** (MongoDB):
   - Name: `MongoDB`
   - URL: `https://<your-mcp-server>.azurecontainerapps.io/mcp`

7. Click **Create**

### 5. Test Your Agent

Try these queries in the Foundry playground:
- "Find movies about hope and redemption"
- "Show me movies from 1994"
- "What are the top 10 highest rated sci-fi movies?"

## MongoDB Atlas Setup

### Load Sample Data

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a cluster (M0 free tier works)
3. Click **...** → **Load Sample Dataset**
4. Wait for `sample_mflix` database to load

### Create Vector Search Index

1. Go to **Atlas Search** → **Create Search Index**
2. Select **JSON Editor**
3. Choose database: `sample_mflix`, collection: `embedded_movies`
4. Index name: `vector_index`
5. Paste this definition:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "plot_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

6. Click **Create Search Index**

### Get Connection String

1. Click **Connect** on your cluster
2. Select **Drivers**
3. Copy the connection string
4. Replace `<password>` with your database user password

## Project Structure

```
mongodb-foundry-agent/
├── README.md
├── docs/
│   ├── architecture.png
│   ├── agent-instructions.md      # Agent system prompt
│   └── openapi-schema.json        # OpenAPI spec for embedding tool
├── src/
│   └── embedding-function/        # Azure Function for embeddings
│       ├── function_app.py
│       ├── host.json
│       └── requirements.txt
├── deploy/
│   ├── mcp-server/
│   │   └── main.bicep             # MongoDB MCP Server deployment
│   └── embedding-function/
│       └── main.bicep             # Embedding Function deployment
└── samples/
    └── queries.md                 # Sample queries to test
```

## Sample Queries

### Semantic Search (Vector)
These use the embedding tool + vector search:
- "Find movies about loss and grief"
- "Movies exploring themes of isolation"
- "Films about family inheritance and legacy"

### Direct Queries
These query MongoDB directly:
- "Show me movies from 1994"
- "Find movies starring Tom Hanks"
- "List all movies rated PG-13"

### Aggregations
These use MongoDB aggregation pipelines:
- "Top 10 highest rated movies"
- "Count of movies by genre"
- "Average runtime of action movies"

## Configuration Options

### Embedding Function

| Setting | Description | Default |
|---------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint | Required |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `EMBEDDING_MODEL` | Embedding model deployment name | `text-embedding-ada-002` |

### MCP Server

| Setting | Description | Default |
|---------|-------------|---------|
| `MDB_MCP_CONNECTION_STRING` | MongoDB connection string | Required |
| `MDB_MCP_READ_ONLY` | Restrict to read operations | `true` |
| `MDB_MCP_HTTP_PORT` | HTTP port | `8080` |

## Cost Estimate

| Component | Tier | Estimated Cost |
|-----------|------|----------------|
| Azure Function | Consumption | ~$0 (free tier) |
| Container App (MCP) | Consumption | ~$0-5/month |
| Azure OpenAI (embeddings) | Pay-as-you-go | ~$0.0001/1K tokens |
| MongoDB Atlas | M0 | Free |
| **Total** | | **~$0-10/month** |

## Troubleshooting

### "Embedding generation failed"
- Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` are set
- Check the embedding model deployment name matches `EMBEDDING_MODEL`
- Ensure the model is deployed in your Azure OpenAI resource

### "MongoDB connection failed"
- Verify the connection string includes username and password
- Check MongoDB Atlas network access allows Azure IPs (or use 0.0.0.0/0 for testing)
- Ensure the MCP server container is running

### "Vector search returned no results"
- Verify the `vector_index` exists on `embedded_movies` collection
- Check the index status is "Active" in Atlas
- Ensure you're using the correct field name (`plot_embedding`)

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
