# MongoDB & Foundry Sample

A deployable code sample demonstrating how to build an intelligent agent with **MongoDB Atlas** and **Azure AI Foundry**.

> **Credit:** This repository is based on and adapted from the original
> [vpriyanshi/mongodb-foundry-agent](https://github.com/vpriyanshi/mongodb-foundry-agent).
> Thanks to the original authors. This copy extends the sample into a guided Developer Day
> workshop (Foundry setup → base agent → evaluations → APIM MCP gateway).

## Sample

| Sample | Description | Key Technologies |
|--------|-------------|------------------|
| [**Simple RAG on Movies**](./samples/simple-rag-movies/) | A 3-step build: a semantic-search movie agent, then agent evaluations, then an APIM MCP gateway | Azure AI Foundry, MongoDB Atlas Vector Search, Azure Container Apps, MCP, Azure API Management |

The sample is structured as a progression so you can build it up step by step:

| Step | Path | What you add |
|------|------|--------------|
| 1. Base agent | [`samples/simple-rag-movies/`](./samples/simple-rag-movies/) | Foundry agent with EmbeddingGenerator (OpenAPI) + MongoDB (MCP) tools |
| 2. Evaluations | [`samples/simple-rag-movies/02-evals/`](./samples/simple-rag-movies/02-evals/) | Portal-visible agent evaluations |
| 3. APIM MCP gateway | [`samples/simple-rag-movies/03-apim-mcp-gateway/`](./samples/simple-rag-movies/03-apim-mcp-gateway/) | Expose the API as a governed MCP server via Azure API Management |

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
└── samples/
    └── simple-rag-movies/             # 3-step build: agent → evals → APIM gateway
        ├── README.md                  # Workshop guide & base agent setup
        ├── src/                       # Source code (Container App REST API)
        ├── deploy/                    # Bicep & ARM templates
        ├── docs/                      # Architecture, agent instructions, OpenAPI spec
        ├── scripts/                   # Deployment & helper scripts
        ├── sample-queries.md          # Example queries to test the agent
        ├── 02-evals/                  # Step 2: agent evaluations
        └── 03-apim-mcp-gateway/       # Step 3: expose the API as an MCP server via APIM
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on adding new samples or improving existing ones.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgements

Adapted from the original repository
[vpriyanshi/mongodb-foundry-agent](https://github.com/vpriyanshi/mongodb-foundry-agent).
This workshop edition restructures and extends that sample for MongoDB Developer Day.

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [MongoDB Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
