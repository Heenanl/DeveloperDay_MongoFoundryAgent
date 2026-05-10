# MongoDB & Foundry Samples

A collection of deployable code samples demonstrating how to build intelligent agents with **MongoDB Atlas** and **Azure AI Foundry**.

## Samples

| Sample | Description | Key Technologies |
|--------|-------------|------------------|
| [**Simple RAG on Movies**](./samples/simple-rag-movies/) | Semantic search over MongoDB movie data using vector embeddings and MCP | Azure AI Foundry, MongoDB Atlas Vector Search, Azure Functions, MCP |
| [**Multimodal Product Search**](./samples/multimodal-product-search/) | Visual product search using text, images, or both with multimodal embeddings | Azure AI Foundry, MongoDB Atlas Vector Search, Voyage AI, Azure Functions, MCP |
| [**Voice Customer Support**](./samples/voice-customer-support/) | Voice-enabled logistics support agent with order tracking, policy search, and ticket creation | Azure AI Foundry, GPT Realtime API, MongoDB Atlas, Azure Functions, MCP |

## Common Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/vpriyanshi/mongodb-foundry-agent.git
   cd mongodb-foundry-agent
   ```

2. Navigate to a sample folder and follow its README:
   ```bash
   cd samples/simple-rag-movies
   ```

## Repository Structure

```
mongodb-foundry-agent/
├── README.md                          # This file — sample catalog
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore
└── samples/
    ├── simple-rag-movies/             # Semantic search agent over movies
    │   ├── README.md                  # Full setup & deployment guide
    │   ├── src/                       # Source code (Azure Function)
    │   ├── deploy/                    # Bicep & ARM templates
    │   ├── docs/                      # Architecture, agent instructions, OpenAPI spec
    │   ├── scripts/                   # Deployment scripts (Bash & PowerShell)
    │   └── sample-queries.md          # Example queries to test the agent
    └── multimodal-product-search/     # Visual product search with images
        ├── README.md                  # Full setup & deployment guide
        ├── src/                       # Embedding function + data loader
        ├── deploy/                    # Bicep & ARM templates
        ├── docs/                      # Agent instructions, OpenAPI spec
        ├── scripts/                   # Deployment scripts (Bash & PowerShell)
        └── sample-queries.md          # Example queries to test the agent
    └── voice-customer-support/        # Voice logistics support agent
        ├── README.md                  # Full setup & deployment guide
        ├── src/                       # Embedding func, ticket func, voice UI, data loader
        ├── deploy/                    # Bicep & ARM templates
        ├── docs/                      # Agent instructions, OpenAPI specs
        ├── scripts/                   # Deployment scripts (Bash & PowerShell)
        └── sample-conversations.md    # Example voice conversations
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on adding new samples or improving existing ones.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
