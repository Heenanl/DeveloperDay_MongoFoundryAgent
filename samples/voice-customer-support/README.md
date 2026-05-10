# Voice Customer Support Agent — SwiftShip Logistics

[← Back to all samples](../../README.md)

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fvpriyanshi%2Fmongodb-foundry-agent%2Fmain%2Fsamples%2Fvoice-customer-support%2Fdeploy%2Fazuredeploy.json)

Build a **voice-enabled customer support agent** for a logistics company using Azure AI Foundry's GPT Realtime API, MongoDB Atlas, and a browser-based voice interface.

## What You'll Build

A voice agent that customers can talk to naturally about their shipments:
- 🎙️ **"Where is my order?"** → Looks up order status and tracking info
- 📦 **"I received a broken item"** → Walks through damage claim process, creates a ticket
- ❌ **"Cancel my order"** → Checks cancellation policy, processes if eligible
- 💰 **"When will my refund arrive?"** → Searches refund policy, provides timeline
- 🎫 **Creates support tickets** when issues can't be resolved automatically

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (Voice UI)                           │
│   Microphone → WebSocket → GPT Realtime API → Speaker              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                     Azure AI Foundry                                │
│         GPT Realtime (gpt-4o-realtime) — Speech-to-Speech           │
│              with Function Calling                                  │
│                  │              │              │                     │
│          ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐             │
│          │ OpenAPI Tool │ │ MCP Tool │ │ OpenAPI Tool│             │
│          │ (Embedding)  │ │(MongoDB) │ │(Ticket API) │             │
│          └───────┬──────┘ └────┬─────┘ └─────┬──────┘             │
└──────────────────┼─────────────┼─────────────┼─────────────────────┘
          ┌────────▼───┐  ┌──────▼──────┐  ┌───▼────────┐
          │ Azure Func │  │ MongoDB MCP │  │ Azure Func │
          │(Embeddings)│  │ Server(ACA) │  │(Ticket API)│
          └────────┬───┘  └──────┬──────┘  └───┬────────┘
                   │       ┌─────▼──────┐      │
                   └──────►│MongoDB Atlas│◄────┘
                           │ • orders    │
                           │ • tickets   │
                           │ • policies  │
                           └─────────────┘
```

## Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com) with **gpt-4o-realtime** model deployed
- [Azure OpenAI resource](https://learn.microsoft.com/azure/ai-services/openai/) with **text-embedding-3-small** deployed
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- [Python 3.11+](https://python.org)

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/vpriyanshi/mongodb-foundry-agent.git
cd mongodb-foundry-agent/samples/voice-customer-support
```

### 2. Deploy Infrastructure

```bash
az login

az group create --name voice-support-rg --location eastus

# Deploy MCP Server
az deployment group create \
  --resource-group voice-support-rg \
  --template-file deploy/mcp-server/main.bicep \
  --parameters mdbConnectionString="<YOUR_MONGODB_CONNECTION_STRING>"

# Deploy Embedding Function
az deployment group create \
  --resource-group voice-support-rg \
  --template-file deploy/embedding-function/main.bicep \
  --parameters azureOpenAIEndpoint="<ENDPOINT>" azureOpenAIKey="<KEY>"

# Deploy Ticket Function
az deployment group create \
  --resource-group voice-support-rg \
  --template-file deploy/ticket-function/main.bicep \
  --parameters mongodbConnectionString="<YOUR_MONGODB_CONNECTION_STRING>"
```

### 3. Deploy Function Code

```bash
cd src/embedding-function && func azure functionapp publish <EMBED_FUNC_NAME> && cd ../..
cd src/ticket-function && func azure functionapp publish <TICKET_FUNC_NAME> && cd ../..
```

### 4. Load Sample Data

```bash
pip install -r src/data-loader/requirements.txt

python src/data-loader/load_data.py \
  --connection-string "<YOUR_MONGODB_CONNECTION_STRING>" \
  --azure-openai-endpoint "<ENDPOINT>" \
  --azure-openai-key "<KEY>"
```

This loads ~20 sample orders and ~10 policy documents (with vector embeddings) into the `swiftship` database.

### 5. Create the Agent in Azure AI Foundry

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project → **Agents** → **+ New Agent**
3. Configure:
   - **Name**: `swiftship-support-agent`
   - **Model**: `gpt-4o-realtime` (for voice) or `gpt-4.1` (for text-only testing)
   - **Instructions**: Copy from [agent-instructions.md](./docs/agent-instructions.md)

4. Add **OpenAPI Tool** (Embedding Generator):
   - Schema: [openapi-embedding.json](./docs/openapi-embedding.json) (update server URL)

5. Add **OpenAPI Tool** (Ticket API):
   - Schema: [openapi-ticket.json](./docs/openapi-ticket.json) (update server URL)

6. Add **MCP Tool** (MongoDB):
   - URL: `https://<your-mcp-server>.azurecontainerapps.io/mcp`

### 6. Test with Voice UI

Open `src/voice-ui/index.html` in a browser:
1. Enter your Azure OpenAI endpoint and `gpt-4o-realtime` deployment name
2. Click **Connect**
3. Click the **mic button** and start talking!

See [sample-conversations.md](./sample-conversations.md) for example dialogues.

## MongoDB Collections

### `orders` — Customer orders
| Field | Description |
|-------|-------------|
| `_id` | Order ID (e.g., `ORD-2024-1001`) |
| `customer_name` | Customer full name |
| `status` | `processing`, `shipped`, `in_transit`, `delivered`, `cancelled`, `returned` |
| `tracking_number` | Carrier tracking number |
| `carrier` | UPS, FedEx, USPS, DHL |
| `estimated_delivery` | Expected delivery date |
| `items` | Array of ordered items with name, qty, price |
| `total` | Order total |

### `tickets` — Support tickets (created by agent)
| Field | Description |
|-------|-------------|
| `_id` | Ticket ID (e.g., `TKT-20260510-001`) |
| `order_id` | Related order ID |
| `issue_type` | `damaged_item`, `cancellation`, `refund`, `lost_package`, `general` |
| `status` | `open`, `in_progress`, `resolved`, `closed` |
| `priority` | `high`, `medium`, `low` |

### `policies` — Knowledge base with vector search
| Field | Description |
|-------|-------------|
| `title` | Policy document title |
| `category` | Policy category |
| `content` | Full policy text |
| `embedding` | Vector embedding for semantic search |

## Sample Structure

```
voice-customer-support/
├── README.md
├── sample-conversations.md
├── src/
│   ├── embedding-function/          # Text embedding API
│   ├── ticket-function/             # Ticket creation/lookup API
│   ├── voice-ui/                    # Browser voice interface
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   └── data-loader/                 # Sample data + loader script
│       ├── load_data.py
│       ├── sample_orders.json       # 20 sample orders
│       └── sample_policies.json     # 10 policy documents
├── deploy/
│   ├── azuredeploy.json             # One-click deployment
│   ├── mcp-server/main.bicep
│   ├── embedding-function/main.bicep
│   └── ticket-function/main.bicep
├── docs/
│   ├── agent-instructions.md        # Voice-optimized system prompt
│   ├── openapi-embedding.json       # Embedding API spec
│   └── openapi-ticket.json          # Ticket API spec
└── scripts/
    ├── deploy.sh
    └── deploy.ps1
```

## Configuration

### Embedding Function
| Setting | Description | Default |
|---------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | Required |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `EMBEDDING_MODEL` | Model deployment name | `text-embedding-3-small` |

### Ticket Function
| Setting | Description | Default |
|---------|-------------|---------|
| `MONGODB_CONNECTION_STRING` | MongoDB Atlas connection string | Required |
| `MONGODB_DATABASE` | Database name | `swiftship` |

### MCP Server
| Setting | Description | Default |
|---------|-------------|---------|
| `MDB_MCP_CONNECTION_STRING` | MongoDB connection string | Required |
| `MDB_MCP_READ_ONLY` | Read-only mode | `false` |

## Cost Estimate

| Component | Tier | Estimated Cost |
|-----------|------|----------------|
| Azure Function (Embedding) | Consumption | ~$0 |
| Azure Function (Ticket) | Consumption | ~$0 |
| Container App (MCP) | Consumption | ~$0-5/month |
| Azure OpenAI (embedding) | Pay-as-you-go | ~$0.02/1M tokens |
| Azure OpenAI (realtime) | Pay-as-you-go | ~$5/1M audio tokens |
| MongoDB Atlas | M0 | Free |
| **Total** | | **~$5-15/month** |

## Troubleshooting

### Voice UI won't connect
- Ensure `gpt-4o-realtime` is deployed in your Azure OpenAI resource
- Check the endpoint URL format (should be `{resource}.openai.azure.com`)
- Verify the API key is correct
- Allow microphone access in your browser

### "Policy search returned no results"
- Ensure the data loader ran successfully and created vector embeddings
- Verify the vector index `policy_vector_index` is "Active" in Atlas
- Check the embedding model deployment name matches

### Ticket creation fails
- Verify the ticket function has the correct MongoDB connection string
- Check MongoDB Atlas network access allows Azure IPs
- Ensure `MDB_MCP_READ_ONLY` is set to `false` on the MCP server

## Resources

- [GPT Realtime API Documentation](https://learn.microsoft.com/azure/ai-services/openai/how-to/realtime-audio)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)
- [Voice Agent Accelerator](https://github.com/Azure-Samples/art-voice-agent-accelerator)
