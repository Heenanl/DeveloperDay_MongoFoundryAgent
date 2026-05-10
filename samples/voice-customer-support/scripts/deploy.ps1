# Voice Customer Support Agent - Quick Deployment Script (PowerShell)

param(
    [string]$ResourceGroup = "voice-support-agent-rg",
    [string]$Location = "eastus",
    [Parameter(Mandatory=$true)]
    [string]$MongoDBConnectionString,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIEndpoint,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIKey,
    [string]$EmbeddingModel = "text-embedding-3-small"
)

$ErrorActionPreference = "Stop"

# Resolve sample root directory (one level up from scripts/)
$SampleDir = Split-Path -Parent $PSScriptRoot
Push-Location $SampleDir

Write-Host "=== Voice Customer Support Agent Deployment ===" -ForegroundColor Cyan
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
                 readOnlyMode='false' `
    --query "properties.outputs" -o json | ConvertFrom-Json

$mcpUrl = $mcpOutput.mcpServerUrl.value
Write-Host "MCP Server URL: $mcpUrl" -ForegroundColor Green

Write-Host "=== Deploying Embedding Function ===" -ForegroundColor Yellow
$embedOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/embedding-function/main.bicep `
    --parameters azureOpenAIEndpoint="$AzureOpenAIEndpoint" `
                 azureOpenAIKey="$AzureOpenAIKey" `
                 embeddingModel="$EmbeddingModel" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$embedFuncName = $embedOutput.functionAppName.value
$embedUrl = $embedOutput.functionAppUrl.value
Write-Host "Embedding Function URL: $embedUrl" -ForegroundColor Green

Write-Host "=== Deploying Embedding Function Code ===" -ForegroundColor Yellow
Push-Location src/embedding-function
func azure functionapp publish $embedFuncName
Pop-Location

Write-Host "=== Deploying Ticket Function ===" -ForegroundColor Yellow
$ticketOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/ticket-function/main.bicep `
    --parameters mongodbConnectionString="$MongoDBConnectionString" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$ticketFuncName = $ticketOutput.functionAppName.value
$ticketUrl = $ticketOutput.functionAppUrl.value
Write-Host "Ticket Function URL: $ticketUrl" -ForegroundColor Green

Write-Host "=== Deploying Ticket Function Code ===" -ForegroundColor Yellow
Push-Location src/ticket-function
func azure functionapp publish $ticketFuncName
Pop-Location

Write-Host "=== Loading Sample Data ===" -ForegroundColor Yellow
Push-Location src/data-loader
pip install -r requirements.txt
python load_data.py
Pop-Location

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MCP Server URL:          $mcpUrl"
Write-Host "Embedding API URL:       $embedUrl"
Write-Host "Ticket Function URL:     $ticketUrl"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://ai.azure.com"
Write-Host "2. Create a new agent"
Write-Host "3. Add MCP tool with URL: $mcpUrl"
Write-Host "4. Add OpenAPI tool for embeddings: $embedUrl"
Write-Host "5. Add OpenAPI tool for tickets: $ticketUrl"
Write-Host "6. Copy instructions from docs/agent-instructions.md"
Write-Host ""

# Restore original directory
Pop-Location

# Return URLs for programmatic use
return @{
    McpServerUrl    = $mcpUrl
    EmbeddingUrl    = $embedUrl
    TicketUrl       = $ticketUrl
}
