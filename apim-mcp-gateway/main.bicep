// =============================================================================
// Import the Movies REST API (Azure Container App) into an existing APIM service
// so it can be exposed as an MCP server via APIM's native MCP feature.
//
// Pattern: REST API (Container App) -> APIM API import -> APIM "Expose as MCP".
// The inbound policy is intentionally body-free so MCP streaming (tools/list) works.
// =============================================================================

@description('Name of the EXISTING APIM service to import the API into.')
param apimServiceName string

@description('Backend base URL of the Container App REST API (include the /api suffix, no trailing slash).')
param backendBaseUrl string

@description('API identifier (resource name) within APIM.')
param apiId string = 'movies-mcp-api'

@description('API display name shown in the APIM portal.')
param apiDisplayName string = 'Movies MCP API'

@description('API route prefix on the APIM gateway (e.g. https://<apim>.azure-api.net/<apiPath>).')
param apiPath string = 'movies'

@description('Whether a subscription key is required to call the API. Keep false so Foundry/MCP can call without a key.')
param subscriptionRequired bool = false

// Load the OpenAPI spec and the body-safe inbound policy from this folder.
var openApiSpec = loadTextContent('openapi-schema.json')
var inboundPolicyXml = loadTextContent('policy.xml')

resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' existing = {
  name: apimServiceName
}

resource api 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: apiId
  properties: {
    displayName: apiDisplayName
    path: apiPath
    protocols: [
      'https'
    ]
    subscriptionRequired: subscriptionRequired
    serviceUrl: backendBaseUrl
    format: 'openapi+json'
    value: openApiSpec
  }
}

resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: inboundPolicyXml
  }
}

@description('The APIM API name/id that was created.')
output apiName string = api.name

@description('The base path the API is served on within the APIM gateway.')
output apiPath string = apiPath

@description('The APIM gateway URL. The imported API is reachable at <gatewayUrl>/<apiPath>.')
output gatewayUrl string = apim.properties.gatewayUrl
