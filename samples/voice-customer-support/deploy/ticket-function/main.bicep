@description('Location of resources')
param location string = resourceGroup().location

@description('Name of the Function App')
param functionAppName string = 'ticket-func'

@secure()
@description('MongoDB Connection String')
param mongodbConnectionString string

@description('MongoDB Database Name')
param mongodbDatabase string = 'swiftship'

// Variables
var storageAccountName = 'stticket${uniqueString(resourceGroup().id)}'

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
          name: 'MONGODB_CONNECTION_STRING'
          value: mongodbConnectionString
        }
        {
          name: 'MONGODB_DATABASE'
          value: mongodbDatabase
        }
      ]
    }
    httpsOnly: true
  }
}

output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}/api/ticket'
output functionAppName string = functionApp.name
