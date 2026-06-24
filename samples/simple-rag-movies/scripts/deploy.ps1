# MongoDB Vector Search Agent - Quick Deployment Script (PowerShell)
#
# Deploys both Azure Container Apps for the base agent:
#   1. MongoDB MCP Server   (deploy/mcp-server/main.bicep)
#   2. Movies Tool API      (built from src/movies-api via `az containerapp up`)
#
# Models (chat + embeddings) are served by your Azure AI Foundry resource — the Foundry
# endpoint is Azure OpenAI-compatible, so pass the Foundry resource endpoint/key below.

param(
    [string]$ResourceGroup = "mongodb-agent-rg",
    [string]$Location = "eastus",
    [Parameter(Mandatory=$true)]
    [string]$MongoDBConnectionString,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIEndpoint,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIKey,
    [string]$EmbeddingModel = "text-embedding-ada-002",
    [string]$MoviesApiName = "movies-tool-api"
)

$ErrorActionPreference = "Stop"

# Resolve sample root directory (one level up from scripts/)
$SampleDir = Split-Path -Parent $PSScriptRoot
Push-Location $SampleDir

Write-Host "=== MongoDB Vector Search Agent Deployment ===" -ForegroundColor Cyan
Write-Host "Running from: $SampleDir" -ForegroundColor Gray
Write-Host ""

# Check prerequisites
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"
}

Write-Host "=== Creating Resource Group ===" -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location | Out-Null

Write-Host "=== Deploying MongoDB MCP Server ===" -ForegroundColor Yellow
$mcpOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/mcp-server/main.bicep `
    --parameters mdbConnectionString="$MongoDBConnectionString" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$mcpUrl = $mcpOutput.mcpServerUrl.value
Write-Host "MCP Server URL: $mcpUrl" -ForegroundColor Green

Write-Host "=== Deploying Movies Tool API (Container Apps, build from source) ===" -ForegroundColor Yellow
Push-Location src/movies-api
az containerapp up `
    --name $MoviesApiName `
    --resource-group $ResourceGroup `
    --location $Location `
    --source . `
    --target-port 8080 `
    --ingress external `
    --env-vars `
        AZURE_OPENAI_ENDPOINT="$AzureOpenAIEndpoint" `
        AZURE_OPENAI_API_KEY="$AzureOpenAIKey" `
        EMBEDDING_MODEL="$EmbeddingModel" `
        MONGODB_CONNECTION_STRING="$MongoDBConnectionString" | Out-Null
Pop-Location

$apiFqdn = az containerapp show --name $MoviesApiName --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" -o tsv
$apiBaseUrl = "https://$apiFqdn/api"
Write-Host "Movies Tool API: $apiBaseUrl" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MCP Server URL    : $mcpUrl"
Write-Host "Movies Tool API   : $apiBaseUrl"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://ai.azure.com"
Write-Host "2. Create a new agent"
Write-Host "3. Add OpenAPI tool (EmbeddingGenerator) with server URL: $apiBaseUrl"
Write-Host "4. Add MCP tool (MongoDB) with URL: $mcpUrl"
Write-Host "5. Copy instructions from docs/agent-instructions.md"
Write-Host ""

# Restore original directory
Pop-Location

# Return URLs for programmatic use
return @{
    McpServerUrl  = $mcpUrl
    MoviesApiUrl  = $apiBaseUrl
}
