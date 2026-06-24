// =============================================================================
// Step 0 — Provision the Azure AI Foundry account + project + model deployments
// for the simple-rag-movies workshop.
//
// Based on the official Foundry sample:
// https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/40-basic-agent-setup
//
// Differences from the reference template:
//   - Deploys TWO models the workshop needs: a chat model (gpt-4.1) AND an
//     embedding model (text-embedding-ada-002). The two deployments are
//     serialized with dependsOn because Cognitive Services cannot create
//     multiple model deployments on one account in parallel.
//   - Sets disableLocalAuth = false so the embedding service can call the
//     Foundry endpoint with the api-key header (the workshop uses key auth).
//     Set it to true if you switch the embedding service to Entra ID / managed
//     identity auth.
// =============================================================================

@description('Base name for the Azure AI Foundry (AIServices) account. A short unique suffix is appended.')
@maxLength(12)
param aiFoundryName string = 'foundry'

@description('The name of the Foundry project to create.')
param projectName string = 'demo'

@description('The display name of the Foundry project.')
param projectDisplayName string = 'Demo'

@description('The description of the Foundry project.')
param projectDescription string = 'simple-rag-movies workshop project'

@allowed([
  'australiaeast'
  'canadaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'japaneast'
  'koreacentral'
  'norwayeast'
  'polandcentral'
  'southindia'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westus'
  'westus2'
  'westus3'
  'westeurope'
  'southeastasia'
  'brazilsouth'
  'germanywestcentral'
  'italynorth'
  'southafricanorth'
  'southcentralus'
])
@description('Azure region for the Foundry resource and project.')
param location string = 'eastus'

// ---- Chat model ----
@description('Chat model deployment name (reused as the agent model).')
param chatDeploymentName string = 'gpt-4.1'

@description('Chat model name.')
param chatModelName string = 'gpt-4.1'

@description('Chat model version.')
param chatModelVersion string = '2025-04-14'

@description('Chat model SKU name.')
param chatModelSku string = 'GlobalStandard'

@description('Chat model capacity (TPM, in thousands).')
param chatModelCapacity int = 40

// ---- Embedding model ----
@description('Embedding model deployment name (reused by the embedding service).')
param embeddingDeploymentName string = 'text-embedding-ada-002'

@description('Embedding model name.')
param embeddingModelName string = 'text-embedding-ada-002'

@description('Embedding model version.')
param embeddingModelVersion string = '2'

@description('Embedding model SKU name.')
param embeddingModelSku string = 'GlobalStandard'

@description('Embedding model capacity (TPM, in thousands).')
param embeddingModelCapacity int = 120

// Unique-but-stable account name within the resource group.
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 4)
var accountName = toLower('${aiFoundryName}${uniqueSuffix}')

resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: accountName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: toLower(accountName)
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: 'Enabled'
    // Workshop uses api-key auth for the embedding service. Set to true only if
    // you switch that service to Entra ID / managed identity authentication.
    disableLocalAuth: false
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: projectDescription
    displayName: projectDisplayName
  }
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: chatDeploymentName
  sku: {
    name: chatModelSku
    capacity: chatModelCapacity
  }
  properties: {
    model: {
      name: chatModelName
      format: 'OpenAI'
      version: chatModelVersion
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: embeddingDeploymentName
  sku: {
    name: embeddingModelSku
    capacity: embeddingModelCapacity
  }
  properties: {
    model: {
      name: embeddingModelName
      format: 'OpenAI'
      version: embeddingModelVersion
    }
  }
  // Cognitive Services cannot create two model deployments in parallel.
  dependsOn: [
    chatDeployment
  ]
}

@description('Foundry (AIServices) account name.')
output accountName string = account.name

@description('Foundry account endpoint (Azure OpenAI-compatible). Use this for the Movies Tool API AZURE_OPENAI_ENDPOINT.')
output accountEndpoint string = account.properties.endpoint

@description('Foundry project name.')
output projectName string = project.name

@description('Foundry project endpoint for agent/eval SDK tooling (use this as FOUNDRY_PROJECT_ENDPOINT). Uses the services.ai.azure.com host required by the Azure AI Projects SDK.')
output projectEndpoint string = 'https://${toLower(account.name)}.services.ai.azure.com/api/projects/${project.name}'

@description('Chat model deployment name.')
output chatDeploymentName string = chatDeployment.name

@description('Embedding model deployment name.')
output embeddingDeploymentName string = embeddingDeployment.name
