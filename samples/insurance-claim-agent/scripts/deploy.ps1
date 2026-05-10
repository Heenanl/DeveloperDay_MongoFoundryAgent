# Insurance Claim Agent - Quick Deployment Script (PowerShell)

param(
    [string]$ResourceGroup = "insurance-claim-agent-rg",
    [string]$Location = "eastus",
    [Parameter(Mandatory=$true)]
    [string]$MongoDBConnectionString,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIEndpoint,
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAIKey,
    [string]$ImageModel = "gpt-4o",
    [Parameter(Mandatory=$true)]
    [string]$VoyageApiKey,
    [string]$VoyageModel = "voyage-3"
)

$ErrorActionPreference = "Stop"

# Resolve sample root directory (one level up from scripts/)
$SampleDir = Split-Path -Parent $PSScriptRoot
Push-Location $SampleDir

Write-Host "=== Insurance Claim Agent Deployment ===" -ForegroundColor Cyan
Write-Host "Running from: $SampleDir" -ForegroundColor Gray
Write-Host ""

# Check prerequisites
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required. Install from https://docs.microsoft.com/cli/azure/install-azure-cli"
}

if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
    throw "Azure Functions Core Tools required. Install from https://docs.microsoft.com/azure/azure-functions/functions-run-local"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ is required. Install from https://python.org"
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

Write-Host "=== Deploying Image Analysis Function ===" -ForegroundColor Yellow
$imageOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/image-analysis-function/main.bicep `
    --parameters azureOpenAIEndpoint="$AzureOpenAIEndpoint" `
                 azureOpenAIKey="$AzureOpenAIKey" `
                 imageModel="$ImageModel" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$imageFuncName = $imageOutput.functionAppName.value
$imageUrl = $imageOutput.functionAppUrl.value
Write-Host "Image Analysis Function URL: $imageUrl" -ForegroundColor Green

Write-Host "=== Deploying Image Analysis Function Code ===" -ForegroundColor Yellow
Push-Location src/image-analysis-function
func azure functionapp publish $imageFuncName
Pop-Location

Write-Host "=== Deploying Embedding Function ===" -ForegroundColor Yellow
$embedOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file deploy/embedding-function/main.bicep `
    --parameters voyageApiKey="$VoyageApiKey" `
                 voyageModel="$VoyageModel" `
    --query "properties.outputs" -o json | ConvertFrom-Json

$embedFuncName = $embedOutput.functionAppName.value
$embedUrl = $embedOutput.functionAppUrl.value
Write-Host "Embedding Function URL: $embedUrl" -ForegroundColor Green

Write-Host "=== Deploying Embedding Function Code ===" -ForegroundColor Yellow
Push-Location src/embedding-function
func azure functionapp publish $embedFuncName
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
Write-Host "MCP Server URL:              $mcpUrl"
Write-Host "Image Analysis Function URL: $imageUrl"
Write-Host "Embedding Function URL:      $embedUrl"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://ai.azure.com"
Write-Host "2. Create the Filing Agent:"
Write-Host "   - Model: gpt-4o"
Write-Host "   - Add OpenAPI tool (Image Analyzer): $imageUrl"
Write-Host "   - Add MCP tool (MongoDB): $mcpUrl"
Write-Host "   - Instructions: docs/agent-instructions-filing.md"
Write-Host "3. Create the Assessment Agent:"
Write-Host "   - Model: gpt-4.1"
Write-Host "   - Add OpenAPI tool (Embedding Generator): $embedUrl"
Write-Host "   - Add MCP tool (MongoDB): $mcpUrl"
Write-Host "   - Instructions: docs/agent-instructions-assessment.md"
Write-Host ""

# Restore original directory
Pop-Location

# Return URLs for programmatic use
return @{
    McpServerUrl     = $mcpUrl
    ImageAnalysisUrl = $imageUrl
    EmbeddingUrl     = $embedUrl
}
