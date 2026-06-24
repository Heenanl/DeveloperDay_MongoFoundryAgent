// =============================================================================
// Provision an Azure API Management service for the Movies MCP gateway.
//
// Default SKU: BasicV2 — a v2 tier designed for development/testing that deploys
// in minutes (the classic 'Developer' tier can take 30-45 min). Switch the `sku`
// parameter to 'Developer', 'StandardV2', etc. if you need a different tier.
//
// NOTE: the v2 tiers (BasicV2 / StandardV2 / PremiumV2) require API version
// 2024-05-01 or later, which this template uses.
//
// After this deploys, import the Movies REST API with main.bicep, then expose it
// as an MCP server (see README).
// =============================================================================

@description('Name of the APIM service to create (must be globally unique).')
param apimServiceName string = 'movies-apim-${uniqueString(resourceGroup().id)}'

@description('Location for the APIM service.')
param location string = resourceGroup().location

@description('APIM SKU. BasicV2 is recommended for workshops (fast deploy, has an SLA). There is no "Developer v2" SKU; use Developer for the classic dev tier.')
@allowed([
  'BasicV2'
  'StandardV2'
  'Developer'
  'Basic'
  'Standard'
])
param sku string = 'BasicV2'

@description('Number of scale units. Use 1 for BasicV2/Developer in a workshop.')
@minValue(1)
param capacity int = 1

@description('Publisher email shown on the developer portal / notifications.')
param publisherEmail string = 'admin@contoso.com'

@description('Publisher (organization) name.')
param publisherName string = 'Movies Workshop'

resource apim 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: apimServiceName
  location: location
  sku: {
    name: sku
    capacity: capacity
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

@description('The name of the created APIM service (pass this to main.bicep as apimServiceName).')
output apimServiceName string = apim.name

@description('The APIM gateway URL.')
output gatewayUrl string = apim.properties.gatewayUrl
