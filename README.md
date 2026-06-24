# MongoDB & Foundry Sample

A deployable code sample demonstrating how to build an intelligent agent with **MongoDB Atlas** and **Azure AI Foundry**.

## Sample

| Sample | Description | Key Technologies |
|--------|-------------|------------------|
| [**Simple RAG on Movies**](./samples/simple-rag-movies/) | Semantic search over MongoDB movie data using vector embeddings and MCP | Azure AI Foundry, MongoDB Atlas Vector Search, Azure Container Apps, MCP |

## Supporting modules

| Module | Description |
|--------|-------------|
| [**apim-mcp-gateway**](./apim-mcp-gateway/) | Expose the movies REST API as an MCP server through Azure API Management (Bring Your Own AI Gateway) |
| [**aigateway-integration**](./aigateway-integration/) | Connect a Foundry project to models/tools through an APIM AI gateway |

## Common Prerequisites

- [Azure Subscription](https://azure.microsoft.com/free/)
- [Azure AI Foundry Project](https://ai.azure.com)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/Heenanl/mongodb-foundry-agent.git
   cd mongodb-foundry-agent
   ```

2. Navigate to the sample folder and follow its README:
   ```bash
   cd samples/simple-rag-movies
   ```

## Repository Structure

```
mongodb-foundry-agent/
├── README.md                          # This file
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore
├── .github/
│   └── workflows/                     # CI, including agent evaluation workflow
├── apim-mcp-gateway/                  # Expose the REST API as an MCP server via APIM
├── aigateway-integration/             # Foundry ↔ APIM AI gateway connection
└── samples/
    └── simple-rag-movies/             # Semantic search agent over movies
        ├── README.md                  # Full setup & deployment guide
        ├── src/                       # Source code (Container App REST API)
        ├── deploy/                    # Bicep & ARM templates
        ├── docs/                      # Architecture, agent instructions, OpenAPI spec
        ├── evals/                     # Agent evaluation datasets & workflow docs
        ├── scripts/                   # Deployment & helper scripts
        └── sample-queries.md          # Example queries to test the agent
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
