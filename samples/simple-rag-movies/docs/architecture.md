# Architecture

This document describes the architecture of the MongoDB Vector Search Agent.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Azure AI Foundry                                │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Hosted Agent (gpt-4.1)                     │   │
│   │                                                                 │   │
│   │   "Find movies about hope and redemption"                       │   │
│   │                        │                                        │   │
│   │           ┌────────────┴────────────┐                          │   │
│   │           ▼                         ▼                          │   │
│   │   ┌──────────────┐         ┌──────────────┐                    │   │
│   │   │ OpenAPI Tool │         │   MCP Tool   │                    │   │
│   │   │ (Embeddings) │         │  (MongoDB)   │                    │   │
│   │   └──────┬───────┘         └──────┬───────┘                    │   │
│   └──────────┼─────────────────────────┼────────────────────────────┘   │
│              │                         │                                │
└──────────────┼─────────────────────────┼────────────────────────────────┘
               │                         │
               ▼                         ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │ Movies Tool API  │      │   Azure Container    │
    │ (Container Apps) │      │   Apps (MCP Server)  │
    │             │                           │
    │  POST /api/embed │      │   /mcp endpoint      │
    └────────┬────────┘      └──────────┬───────────┘
             │                           │
             ▼                           ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │ Azure AI Foundry │      │   MongoDB Atlas      │
    │ models           │      │                      │
    │ text-embedding-  │      │ sample_mflix DB      │
    │ ada-002          │      │ • movies             │
    │ (1536 dims)      │      │ • embedded_movies    │
    └──────────────────┘      │   (with vector idx)  │
                              └──────────────────────┘
```

## Components

### 1. Azure AI Foundry Agent
- **Model**: gpt-4.1 (or any compatible model)
- **Role**: Orchestrates tool calls based on user queries
- **Decision Logic**: Chooses between direct queries and vector search

### 2. Movies Tool API (Azure Container Apps)
- **Runtime**: Python 3.11 Flask container (`server.py` + `Dockerfile`)
- **Input**: Text string (for `/api/embed`)
- **Output**: 1536-dimensional embedding vector
- **Uses**: An embedding model deployed in your Azure AI Foundry project (e.g. text-embedding-ada-002)
- **Note**: Also serves `/api/mongo/*` REST routes used by the APIM step (Step 3); the base agent only calls `/api/embed`.

### 3. MongoDB MCP Server (Azure Container Apps)
- **Image**: mongodb/mongodb-mcp-server:latest
- **Protocol**: HTTP-based MCP (Model Context Protocol)
- **Operations**: find, aggregate, $vectorSearch

### 4. MongoDB Atlas
- **Database**: sample_mflix (MongoDB sample dataset)
- **Collection**: embedded_movies (has plot_embedding field)
- **Index**: vector_index (cosine similarity, 1536 dimensions)

## Data Flow

### Semantic Search Query
```
User: "Find movies about hope"
       │
       ▼
   ┌───────────────┐
   │ Agent decides │─── "This is conceptual, needs vector search"
   │  query type   │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │ Call Embedding│─── POST {"text": "hope"}
   │    Function   │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │ Foundry models│─── Returns [0.012, -0.034, ...]
   │  (ada-002)    │    (1536 floats)
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │  Call MongoDB │─── $vectorSearch with embedding
   │   MCP Server  │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │ MongoDB Atlas │─── Returns top 10 matching movies
   │ Vector Search │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │    Agent      │─── Formats and presents results
   │   Response    │
   └───────────────┘
```

### Direct Query
```
User: "Movies from 1994"
       │
       ▼
   ┌───────────────┐
   │ Agent decides │─── "This is a filter, direct query"
   │  query type   │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │  Call MongoDB │─── find({year: 1994})
   │   MCP Server  │
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │ MongoDB Atlas │─── Returns matching movies
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │    Agent      │
   │   Response    │
   └───────────────┘
```

## Vector Index Configuration

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

## Cost Considerations

| Component | Pricing Model | Typical Cost |
|-----------|---------------|--------------|
| Movies Tool API (Container App) | Consumption (pay-per-vCPU-second) | ~$5/month |
| MCP Server (Container App) | Consumption (pay-per-vCPU-second) | ~$5/month |
| Azure AI Foundry (embeddings) | Per 1K tokens | ~$0.0001/query |
| MongoDB Atlas | M0 (free) to M10+ | $0 - $57+/month |

## Scaling Considerations

- **Movies Tool API**: Container App auto-scales by replica count (set minReplicas/maxReplicas)
- **MCP Server**: Set minReplicas/maxReplicas for predictable scaling
- **MongoDB Atlas**: Choose appropriate tier for query volume
