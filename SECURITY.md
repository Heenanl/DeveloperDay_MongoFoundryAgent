# Security

## Reporting Security Issues

If you discover a security vulnerability, please report it privately via email instead of opening a public issue.

## Security Best Practices

When deploying this sample:

### MongoDB Atlas
- Use IP allowlisting to restrict access to your cluster
- Create a dedicated database user with minimal permissions
- Enable audit logging for production deployments
- Use TLS/SSL for all connections (enabled by default)

### Azure Function (Embedding API)
- Consider adding authentication for production use
- Store API keys in Azure Key Vault instead of App Settings
- Enable managed identity where possible
- Monitor function invocations for abuse

### MCP Server
- Set `MDB_MCP_READ_ONLY=true` to prevent write operations
- Consider enabling Azure AD authentication for production
- Use private endpoints for enhanced security

### Secrets Management
- Never commit secrets to source control
- Use Azure Key Vault for production secrets
- Rotate API keys regularly
- Use managed identities where possible

## Dependencies

This project uses:
- Azure Functions Python runtime
- Azure OpenAI API
- MongoDB MCP Server (official MongoDB image)

Keep all dependencies updated to their latest secure versions.
