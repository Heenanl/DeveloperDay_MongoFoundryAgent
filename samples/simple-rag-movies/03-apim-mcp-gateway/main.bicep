// =============================================================================
// Import the Movies REST API (Azure Container App) into an existing APIM service
// so it can be exposed as an MCP server via APIM's native MCP feature.
//
// Pattern: REST API (Container App) -> APIM API import -> APIM "Expose as MCP".
//
// IMPORTANT: by default this template does NOT attach an API-level policy.
// The portal "Expose an API as an MCP server" wizard fails with
// `Unexpected token '<'` when an API-level policy is present. Import the API
// first (no policy), create the MCP server in the portal, THEN optionally apply
// the body-safe hardening policy by setting applyApiPolicy=true and redeploying.
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

@description('Attach the body-safe API-level policy. Keep FALSE for the initial import so the portal "Expose as MCP" wizard works; set TRUE to apply policy as a later hardening step (after the MCP server is created).')
param applyApiPolicy bool = false

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

resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = if (applyApiPolicy) {
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
