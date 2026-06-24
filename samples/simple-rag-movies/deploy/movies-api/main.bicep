// =============================================================================
// Deploy the Movies Tool API (embedding + MongoDB REST API) to Azure Container Apps.
//
// The API code lives in ../../src/movies-api (Flask `server.py` + Dockerfile)
// and exposes: /api/embed, /api/mongo/vector-search, /api/mongo/find,
// /api/mongo/aggregate, /api/health on port 8080.
//
// This template deploys a PRE-BUILT image. For a workshop, the simplest path is to
// build + deploy from source in one command instead of using this template:
//
//   cd src/movies-api
//   az containerapp up --name movies-tool-api-devday --resource-group <rg> \
//     --location eastus --source . --target-port 8080 --ingress external \
//     --env-vars AZURE_OPENAI_ENDPOINT=<foundry-endpoint> \
//                AZURE_OPENAI_API_KEY=<foundry-key> \
//                EMBEDDING_MODEL=text-embedding-ada-002 \
//                MONGODB_CONNECTION_STRING=<mongo-conn-string>
//
// Use this Bicep when you have already built and pushed the image to a registry.
// =============================================================================

@description('Location of resources')
param location string = resourceGroup().location

@description('Name of the Container App')
param containerAppName string = 'movies-tool-api'

@description('Container image (must be reachable by the Container Apps environment).')
param containerImage string

@description('Container CPU cores')
@allowed(['0.25', '0.5', '1.0'])
param containerCpu string = '0.5'

@description('Container Memory')
@allowed(['0.5Gi', '1Gi', '2Gi'])
param containerMemory string = '1Gi'

@description('Azure AI Foundry resource endpoint (Azure OpenAI-compatible).')
param azureOpenAIEndpoint string

@secure()
@description('A key for the Azure AI Foundry resource.')
param azureOpenAIKey string

@description('Embedding model deployment name in the Foundry project.')
param embeddingModel string = 'text-embedding-ada-002'

@secure()
@description('MongoDB Atlas connection string.')
param mdbConnectionString string

@description('MongoDB database name.')
param mongoDatabase string = 'sample_mflix'

var containerCpuNumber = json(containerCpu)

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-02-02-preview' = {
  name: 'movies-api-env-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {}
}

resource containerApp 'Microsoft.App/containerApps@2024-02-02-preview' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
      }
      secrets: [
        {
          name: 'aoai-key'
          value: azureOpenAIKey
        }
        {
          name: 'mdb-connection-string'
          value: mdbConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'movies-tool-api'
          image: containerImage
          resources: {
            cpu: containerCpuNumber
            memory: containerMemory
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'aoai-key'
            }
            {
              name: 'EMBEDDING_MODEL'
              value: embeddingModel
            }
            {
              name: 'MONGODB_CONNECTION_STRING'
              secretRef: 'mdb-connection-string'
            }
            {
              name: 'MONGODB_DATABASE'
              value: mongoDatabase
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

@description('Base URL of the Movies Tool API (append /api/...).')
output apiBaseUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('The OpenAPI server URL to use for the EmbeddingGenerator tool.')
output apiServerUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}/api'

@description('Health endpoint to verify the deployment.')
output healthUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}/api/health'

output containerAppName string = containerApp.name
