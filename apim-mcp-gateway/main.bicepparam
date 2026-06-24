using 'main.bicep'

// Existing APIM service to import into.
param apimServiceName = '<APIM_SERVICE_NAME>'

// Container App REST backend (include the /api suffix, no trailing slash).
param backendBaseUrl = 'https://<CONTAINER_APP_FQDN>/api'

// APIM API identity / routing.
param apiId = 'movies-mcp-api'
param apiDisplayName = 'Movies MCP API'
param apiPath = 'movies'

// Keep false so Foundry/MCP can call without a subscription key.
param subscriptionRequired = false
