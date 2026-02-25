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
    │  Azure Function  │      │   Azure Container    │
    │ (Embedding API)  │      │   Apps (MCP Server)  │
    │                  │      │                      │
    │  POST /api/embed │      │   /mcp endpoint      │
    └────────┬─────────┘      └──────────┬───────────┘
             │                           │
             ▼                           ▼
    ┌──────────────────┐      ┌──────────────────────┐
    │   Azure OpenAI   │      │   MongoDB Atlas      │
    │                  │      │                      │
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

### 2. Embedding Function (Azure Functions)
- **Runtime**: Python 3.11, Consumption plan
- **Input**: Text string
- **Output**: 1536-dimensional embedding vector
- **Uses**: Azure OpenAI text-embedding-ada-002

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
   │   Azure OpenAI│─── Returns [0.012, -0.034, ...]
   │   (ada-002)   │    (1536 floats)
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
| Azure Function | Consumption (pay-per-execution) | ~$0/month for low usage |
| Container App | Consumption (pay-per-vCPU-second) | ~$5/month |
| Azure OpenAI | Per 1K tokens | ~$0.0001/query |
| MongoDB Atlas | M0 (free) to M10+ | $0 - $57+/month |

## Scaling Considerations

- **Azure Function**: Auto-scales, no configuration needed
- **MCP Server**: Set minReplicas/maxReplicas for predictable scaling
- **MongoDB Atlas**: Choose appropriate tier for query volume
