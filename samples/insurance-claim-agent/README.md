# Insurance Claim Agent — Multi-Agent Workflow with Azure AI Foundry

[← Back to all samples](../../README.md)

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fvpriyanshi%2Fmongodb-foundry-agent%2Fmain%2Fsamples%2Finsurance-claim-agent%2Fdeploy%2Fazuredeploy.json)

Build a **multi-agent insurance claim processing system** using Azure AI Foundry. Two specialized agents handle claim filing (customer-facing, multimodal) and claim assessment (internal, with vector search).

## What You'll Build

A multi-agent system where two specialized agents collaborate on insurance claims:
- 📸 **"I was in an accident"** → Filing Agent analyzes photo, collects details, creates claim
- 🔍 **"Assess claim CLM-20250615-001"** → Assessment Agent loads claim, searches policies, generates assessment
- 📋 **Structured assessments** with coverage determination, payout estimates, recommendations
- 🗄️ **MongoDB Atlas** for claim storage and vector-powered policy search

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Azure AI Foundry                             │
│                                                                      │
│  ┌──────────────────────────┐   ┌──────────────────────────────┐    │
│  │     Filing Agent         │   │     Assessment Agent          │    │
│  │       (GPT-4o)           │   │       (GPT-4.1)               │    │
│  │                          │   │                                │    │
│  │  ┌──────────┐ ┌───────┐  │   │  ┌────────────┐ ┌───────┐    │    │
│  │  │ OpenAPI  │ │  MCP  │  │   │  │  OpenAPI   │ │  MCP  │    │    │
│  │  │(ImageAn.)│ │(Mongo)│  │   │  │(Embedding) │ │(Mongo)│    │    │
│  │  └────┬─────┘ └───┬───┘  │   │  └─────┬──────┘ └───┬───┘    │    │
│  └───────┼────────────┼──────┘   └────────┼────────────┼────────┘    │
└──────────┼────────────┼───────────────────┼────────────┼─────────────┘
    ┌──────▼──────┐  ┌──▼───────────┐  ┌───▼──────┐     │
    │ Azure Func  │  │ MongoDB MCP  │  │Azure Func│     │
    │(Image Anal.)│  │ Server (ACA) │  │(Embeddin)│     │
    └─────────────┘  └──────┬───────┘  └──────────┘     │
                      ┌─────▼───────────┐               │
                      │  MongoDB Atlas   │◄──────────────┘
                      │ • claims         │
                      │ • policy_docs    │
                      └─────────────────┘
```

## Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com)
- [Azure OpenAI resource](https://learn.microsoft.com/azure/ai-services/openai/) with **GPT-4o** deployed
- [Voyage AI API key](https://www.voyageai.com/)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- [Python 3.11+](https://python.org)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/vpriyanshi/mongodb-foundry-agent.git
cd mongodb-foundry-agent/samples/insurance-claim-agent
```

### 2. Deploy Infrastructure

```bash
az login

az group create --name insurance-claim-rg --location eastus

# Deploy MCP Server
az deployment group create \
  --resource-group insurance-claim-rg \
  --template-file deploy/mcp-server/main.bicep \
  --parameters mdbConnectionString="<YOUR_MONGODB_CONNECTION_STRING>" \
               readOnlyMode=false

# Deploy Image Analysis Function
az deployment group create \
  --resource-group insurance-claim-rg \
  --template-file deploy/image-analysis-function/main.bicep \
  --parameters azureOpenAIEndpoint="<ENDPOINT>" \
               azureOpenAIKey="<KEY>" \
               imageModel="gpt-4o"

# Deploy Embedding Function
az deployment group create \
  --resource-group insurance-claim-rg \
  --template-file deploy/embedding-function/main.bicep \
  --parameters voyageApiKey="<VOYAGE_API_KEY>" \
               voyageModel="voyage-3"
```

### 3. Deploy Function Code

```bash
cd src/image-analysis-function && func azure functionapp publish <IMAGE_FUNC_NAME> && cd ../..
cd src/embedding-function && func azure functionapp publish <EMBED_FUNC_NAME> && cd ../..
```

### 4. Load Sample Data

```bash
cd src/data-loader
pip install -r requirements.txt
python load_data.py
cd ../..
```

This loads sample claims and policy documents (with vector embeddings) into the `insurance` database.

### 5. Create the Filing Agent in Azure AI Foundry

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project → **Agents** → **+ New Agent**
3. Configure:
   - **Name**: `insurance-filing-agent`
   - **Model**: `gpt-4o`
   - **Instructions**: Copy from [agent-instructions-filing.md](./docs/agent-instructions-filing.md)

4. Add **OpenAPI Tool** (Image Analyzer):
   - Schema: [openapi-image-analysis.json](./docs/openapi-image-analysis.json) (update server URL)

5. Add **MCP Tool** (MongoDB):
   - URL: `https://<your-mcp-server>.azurecontainerapps.io/mcp`

### 6. Create the Assessment Agent in Azure AI Foundry

1. Open your project → **Agents** → **+ New Agent**
2. Configure:
   - **Name**: `insurance-assessment-agent`
   - **Model**: `gpt-4.1`
   - **Instructions**: Copy from [agent-instructions-assessment.md](./docs/agent-instructions-assessment.md)

3. Add **OpenAPI Tool** (Embedding Generator):
   - Schema: [openapi-embedding.json](./docs/openapi-embedding.json) (update server URL)

4. Add **MCP Tool** (MongoDB):
   - URL: `https://<your-mcp-server>.azurecontainerapps.io/mcp`

## MongoDB Collections

### `claims` — Insurance claims

| Field | Description |
|-------|-------------|
| `_id` | Claim ID (e.g., `CLM-20250615-001`) |
| `policy_number` | Associated policy number |
| `customer_name` | Customer full name |
| `accident_date` | Date of the incident |
| `location` | Incident location |
| `description` | Customer's account of the incident |
| `vehicles_involved` | Array of vehicles in the incident |
| `injuries` | Reported injuries |
| `police_report_number` | Police report reference |
| `image_analysis` | AI-generated analysis of submitted photos |
| `status` | `filed`, `under_review`, `assessed`, `approved`, `denied`, `closed` |
| `created_at` | Claim creation timestamp |
| `assessment` | Assessment results (added by Assessment Agent) |

### `policy_documents` — Knowledge base with vector search

| Field | Description |
|-------|-------------|
| `_id` | Document ID |
| `title` | Policy document title |
| `category` | Policy category (e.g., `auto`, `home`, `liability`) |
| `coverage_type` | Type of coverage |
| `content` | Full policy text |
| `effective_date` | Policy effective date |
| `embedding` | Vector embedding for semantic search (1024 dimensions) |

## Vector Index Setup

Create the following vector index in MongoDB Atlas on the `policy_documents` collection:

```json
{
  "name": "policy_vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
}
```

## Sample Structure

```
insurance-claim-agent/
├── README.md
├── src/
│   ├── image-analysis-function/     # Image analysis API (GPT-4o vision)
│   ├── embedding-function/          # Voyage AI embedding API
│   └── data-loader/                 # Sample data + loader script
│       ├── load_data.py
│       ├── sample_claims.json
│       └── sample_policies.json
├── deploy/
│   ├── azuredeploy.json             # One-click deployment
│   ├── mcp-server/main.bicep
│   ├── image-analysis-function/main.bicep
│   └── embedding-function/main.bicep
├── docs/
│   ├── agent-instructions-filing.md      # Filing agent system prompt
│   ├── agent-instructions-assessment.md  # Assessment agent system prompt
│   ├── openapi-image-analysis.json       # Image analysis API spec
│   └── openapi-embedding.json            # Embedding API spec
└── scripts/
    ├── deploy.sh
    └── deploy.ps1
```

## Configuration

### Image Analysis Function

| Setting | Description | Default |
|---------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | Required |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `IMAGE_MODEL` | Model deployment name | `gpt-4o` |

### Embedding Function

| Setting | Description | Default |
|---------|-------------|---------|
| `VOYAGE_API_KEY` | Voyage AI API key | Required |
| `VOYAGE_MODEL` | Voyage model name | `voyage-3` |

### MCP Server

| Setting | Description | Default |
|---------|-------------|---------|
| `MDB_MCP_CONNECTION_STRING` | MongoDB connection string | Required |
| `MDB_MCP_READ_ONLY` | Read-only mode | `false` |

## Cost Estimate

| Component | Tier | Estimated Cost |
|-----------|------|----------------|
| Azure Function (Image Analysis) | Consumption | ~$0 |
| Azure Function (Embedding) | Consumption | ~$0 |
| Container App (MCP) | Consumption | ~$0-5/month |
| Azure OpenAI (GPT-4o vision) | Pay-as-you-go | ~$5/1M tokens |
| Voyage AI (embeddings) | Pay-as-you-go | ~$0.06/1M tokens |
| MongoDB Atlas | M0 | Free |
| **Total** | | **~$5-15/month** |

## Troubleshooting

### Image analysis fails
- Ensure GPT-4o is deployed in your Azure OpenAI resource
- Verify the endpoint URL format (should be `{resource}.openai.azure.com`)
- Check that the API key is correct
- Confirm the image is a supported format (JPEG, PNG, WebP)

### Policy search returned no results
- Ensure the data loader ran successfully and created vector embeddings
- Verify the vector index `policy_vector_index` is "Active" in Atlas
- Check the Voyage AI API key is valid and has quota

### Claim creation fails
- Verify the MCP server has the correct MongoDB connection string
- Check MongoDB Atlas network access allows Azure IPs
- Ensure `MDB_MCP_READ_ONLY` is set to `false` on the MCP server

### Assessment agent can't find claim
- Confirm the claim ID format is correct (`CLM-YYYYMMDD-NNN`)
- Verify the claim was created successfully in the `claims` collection
- Check that the MCP server is running and accessible

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)
- [Voyage AI Documentation](https://docs.voyageai.com/)
