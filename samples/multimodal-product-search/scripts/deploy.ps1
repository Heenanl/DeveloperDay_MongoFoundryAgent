# Multimodal Product Search - Deployment Script (PowerShell)

param(
    [string]$ResourceGroup = "multimodal-search-rg",
    [string]$Location = "eastus",
    [Parameter(Mandatory=$true)]
    [string]$MongoDBConnectionString,
    [Parameter(Mandatory=$true)]
    [string]$VoyageApiKey,
    [string]$VoyageModel = "voyage-multimodal-3"
)

$ErrorActionPreference = "Stop"

# Resolve sample root directory
$SampleDir = Split-Path -Parent $PSScriptRoot
Push-Location $SampleDir

Write-Host "=== Multimodal Product Search - Deployment ===" -ForegroundColor Cyan
Write-Host "Running from: $SampleDir" -ForegroundColor Gray
Write-Host ""

# Check prerequisites
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"
}

if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
    throw "Azure Functions Core Tools required. Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"
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

Write-Host "=== Deploying Embedding Function ===" -ForegroundColor Yellow
$funcOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/embedding-function/main.bicep `
    --parameters voyageApiKey="$VoyageApiKey" `
                 voyageModel="$VoyageModel" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$funcName = $funcOutput.functionAppName.value
$embedUrl = $funcOutput.functionAppUrl.value
Write-Host "Embedding Function URL: $embedUrl" -ForegroundColor Green

Write-Host "=== Deploying Function Code ===" -ForegroundColor Yellow
Push-Location src/embedding-function
func azure functionapp publish $funcName
Pop-Location

Write-Host "=== Loading Sample Product Data ===" -ForegroundColor Yellow
pip install -r src/data-loader/requirements.txt --quiet
python src/data-loader/load_products.py `
    --connection-string "$MongoDBConnectionString" `
    --voyage-api-key "$VoyageApiKey"

# Restore original directory
Pop-Location

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MCP Server URL: $mcpUrl"
Write-Host "Embedding API URL: $embedUrl"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://ai.azure.com"
Write-Host "2. Create a new agent"
Write-Host "3. Add OpenAPI tool with URL: $embedUrl"
Write-Host "4. Add MCP tool with URL: $mcpUrl"
Write-Host "5. Copy instructions from docs/agent-instructions.md"
Write-Host ""

return @{
    McpServerUrl = $mcpUrl
    EmbeddingUrl = $embedUrl
}
