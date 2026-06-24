# Contributing

Thank you for your interest in contributing to this project!

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-new-feature`
3. **Make your changes**
4. **Test your changes** thoroughly
5. **Commit your changes**: `git commit -am 'Add some feature'`
6. **Push to the branch**: `git push origin feature/my-new-feature`
7. **Submit a Pull Request**

## Development Setup

1. Clone the repository
2. Run the Movies Tool API locally from `src/movies-api`:
   ```bash
   cd samples/simple-rag-movies/src/movies-api
   pip install -r requirements.txt
   ```
3. Set the required environment variables (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`,
   `EMBEDDING_MODEL`, `MONGODB_CONNECTION_STRING`) — point them at your Azure AI Foundry resource.
4. Run the API: `python server.py` (listens on port 8080)

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write tests for new functionality

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Include your environment details (OS, Python version, etc.)
- Include relevant logs or error messages

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone.
