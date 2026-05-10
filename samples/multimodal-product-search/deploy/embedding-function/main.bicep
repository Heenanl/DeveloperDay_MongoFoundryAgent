@description('Location of resources')
param location string = resourceGroup().location

@description('Name of the Function App')
param functionAppName string = 'multimodal-embed-func'

@secure()
@description('Voyage AI API Key for embeddings')
param voyageApiKey string

@description('Voyage AI Model Name')
param voyageModel string = 'voyage-multimodal-3'

// Variables
var storageAccountName = 'st${uniqueString(resourceGroup().id)}'

// Storage Account (required for Function App)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

// App Service Plan (Consumption)
resource hostingPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${functionAppName}-plan'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true // Linux
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      pythonVersion: '3.11'
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'VOYAGE_API_KEY'
          value: voyageApiKey
        }
        {
          name: 'VOYAGE_MODEL'
          value: voyageModel
        }
      ]
    }
    httpsOnly: true
  }
}

output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}/api/embed-multimodal'
output functionAppName string = functionApp.name
