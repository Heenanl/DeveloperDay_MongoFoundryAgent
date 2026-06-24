# Simple RAG on Movies — MongoDB Vector Search Agent with Azure AI Foundry

[← Back to all samples](../../README.md)

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fvpriyanshi%2Fmongodb-foundry-agent%2Fmain%2Fsamples%2Fsimple-rag-movies%2Fdeploy%2Fazuredeploy.json)

Build an intelligent agent that performs semantic search over MongoDB movie data using Azure AI Foundry and the MongoDB MCP Server.

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
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) — create via [Azure Native Integration](#option-a-create-mongodb-atlas-via-azure-native-integration) (recommended) or [Atlas Portal](#option-b-create-mongodb-atlas-via-atlas-portal), with:
  - `sample_mflix` sample database loaded
  - Vector search index created (see [MongoDB Atlas Setup](#mongodb-atlas-setup))
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/vpriyanshi/mongodb-foundry-agent.git
cd mongodb-foundry-agent/samples/simple-rag-movies
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
  --storage-account embeddingfuncstore512965 \
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

See [sample-queries.md](./sample-queries.md) for more examples.

## MongoDB Atlas Setup

You can provision MongoDB Atlas in two ways:
- **Option A** — [Azure Native Integration](#option-a-create-mongodb-atlas-via-azure-native-integration) (recommended): Create and manage MongoDB Atlas directly from the Azure portal, with unified billing on your Azure invoice.
- **Option B** — [MongoDB Atlas Portal](#option-b-create-mongodb-atlas-via-atlas-portal): Create a cluster directly on [cloud.mongodb.com](https://cloud.mongodb.com).

Both options produce the same result — a MongoDB Atlas cluster with sample data and a vector search index. Choose whichever fits your workflow.

---

### Option A: Create MongoDB Atlas via Azure Native Integration

> **Why this approach?** Azure Native Integration lets you provision, manage, and monitor MongoDB Atlas as a first-class Azure resource. Billing is consolidated into your Azure invoice, and you can use Azure RBAC, tags, and resource groups to manage the resource alongside your other Azure services.

#### Prerequisites
- An active [Azure subscription](https://azure.microsoft.com/free/) with **Owner** or **Contributor** role
- (Optional) An existing [MongoDB Atlas account](https://www.mongodb.com/cloud/atlas) — one will be linked or created during setup

#### Step 1: Create the MongoDB Atlas Resource in Azure Portal

1. Sign in to the [Azure portal](https://portal.azure.com)
2. Click **Create a resource** (or search for **MongoDB Atlas** in the top search bar)
3. Select **MongoDB Atlas (Azure Native ISV Service)** from the Marketplace results
4. Click **Create** and fill in the **Basics** tab:

   | Field | Value |
   |---|---|
   | **Subscription** | Select your Azure subscription |
   | **Resource group** | Use an existing one or create new (e.g., `mongodb-agent-rg`) |
   | **Resource name** | A globally unique name for your Atlas resource |
   | **Region** | Select the Azure region (e.g., `East US`) |
   | **Organization name** | Your MongoDB Atlas organization name |

5. (Optional) Add **Tags** for resource management
6. Click **Review + create** → **Create**
7. Wait for deployment to complete, then click **Go to resource**

#### Step 2: Set Up Your Cluster in Atlas

1. On the resource overview page, click **Go to MongoDB Atlas** — this opens the Atlas portal linked to your Azure account
2. If you don't already have a cluster, create one:
   - Select **Build a Cluster** → choose **M0 (Free)** tier for testing
   - Select the same Azure region as your resource for lowest latency
   - Click **Create Cluster**

#### Step 3: Load Sample Data

1. In the Atlas portal, find your cluster and click **...** (ellipsis menu)
2. Select **Load Sample Dataset**
3. Wait for the `sample_mflix` database to load (this takes a few minutes)

#### Step 4: Create Vector Search Index

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
7. Wait for the index status to show **Active**

#### Step 5: Get Connection String

1. Go back to your cluster and click **Connect**
2. Select **Drivers**
3. Copy the connection string
4. Replace `<password>` with your database user password

> **Tip:** You can also find connection details from the Azure portal resource page under **Connection strings**.

#### Additional Resources

- [Quickstart: Create a MongoDB Atlas resource in Azure](https://learn.microsoft.com/azure/partner-solutions/mongodb-atlas/create)
- [Manage MongoDB Atlas through Azure](https://learn.microsoft.com/azure/partner-solutions/mongodb-atlas/manage)

---

### Option B: Create MongoDB Atlas via Atlas Portal

If you prefer to use the MongoDB Atlas portal directly (or already have an existing cluster):

#### Load Sample Data

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a cluster (M0 free tier works)
3. Click **...** → **Load Sample Dataset**
4. Wait for `sample_mflix` database to load

#### Create Vector Search Index

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

#### Get Connection String

1. Click **Connect** on your cluster
2. Select **Drivers**
3. Copy the connection string
4. Replace `<password>` with your database user password

## Sample Structure

```
simple-rag-movies/
├── README.md                          # This file
├── sample-queries.md                  # Example queries to test
├── src/
│   └── embedding-function/            # Azure Function for embeddings
│       ├── function_app.py
│       ├── host.json
│       ├── local.settings.json.template
│       └── requirements.txt
├── deploy/
│   ├── azuredeploy.json               # One-click ARM deployment
│   ├── mcp-server/
│   │   └── main.bicep                 # MongoDB MCP Server deployment
│   └── embedding-function/
│       └── main.bicep                 # Embedding Function deployment
├── docs/
│   ├── architecture.png               # Architecture diagram
│   ├── architecture.md                # Detailed architecture doc
│   ├── agent-instructions.md          # Agent system prompt
│   └── openapi-schema.json            # OpenAPI spec for embedding tool
└── scripts/
    ├── deploy.sh                      # Bash deployment script
    └── deploy.ps1                     # PowerShell deployment script
```

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

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
