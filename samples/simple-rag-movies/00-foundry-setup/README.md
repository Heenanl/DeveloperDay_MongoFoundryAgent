# Step 0 — Azure AI Foundry Setup

[← Back to the simple-rag-movies guide](../README.md)

> **Step 0 of the [simple-rag-movies](../README.md) workshop.** Provision Azure AI Foundry and the
> model deployments first, then build the base agent, then add [evaluations](../02-evals/) and the
> [APIM MCP gateway](../03-apim-mcp-gateway/).

> **Already have a Foundry resource?** You can either:
> - **Use your own** existing Azure AI Foundry account + project — just make sure it has a chat
>   deployment (`gpt-4.1`) and an embedding deployment (`text-embedding-ada-002`), and note the
>   project endpoint and deployment names; **or**
> - **Self-provision** everything with the Bicep below (recommended if you're starting fresh).

This step provisions everything the agent needs from Azure AI Foundry:

- an **Azure AI Foundry (AIServices) account**
- a **project** (default name `demo`)
- a **chat** model deployment — `gpt-4.1`
- an **embedding** model deployment — `text-embedding-ada-002`

It is based on the official Foundry sample
[`40-basic-agent-setup`](https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/40-basic-agent-setup),
extended to also deploy the embedding model the Movies agent uses for semantic search.

---

## Why both models?

The agent needs two model deployments from the **same Foundry resource**:

| Model | Deployment name | Used by |
|-------|-----------------|---------|
| Chat | `gpt-4.1` | The Foundry agent (and the evaluators' LLM judge) |
| Embedding | `text-embedding-ada-002` | The Movies Tool API `/api/embed` endpoint for vector search |

You do **not** need a separate Azure OpenAI resource — the Foundry resource endpoint is
Azure OpenAI–compatible.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [Azure Subscription](https://azure.microsoft.com/free/) | With **Owner** or **Contributor** on the resource group |
| [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) | `az bicep version` to confirm Bicep is available |
| Quota | Capacity for `gpt-4.1` and `text-embedding-ada-002` in your chosen region |

---

## Deploy

```powershell
az login

# Create (or reuse) a resource group
az group create --name mongodb-agent-rg --location eastus

# Provision Foundry account + project + both model deployments
az deployment group create `
  --resource-group mongodb-agent-rg `
  --template-file main.bicep `
  --parameters projectName=demo
```

### Parameters you can override

| Parameter | Default | Description |
|-----------|---------|-------------|
| `aiFoundryName` | `foundry` | Base name for the account (a short unique suffix is appended) |
| `projectName` | `demo` | Foundry project name |
| `location` | `eastus` | Region for the account, project, and deployments |
| `chatDeploymentName` | `gpt-4.1` | Chat deployment name |
| `chatModelVersion` | `2025-04-14` | Chat model version |
| `chatModelCapacity` | `40` | Chat capacity (TPM, thousands) |
| `embeddingDeploymentName` | `text-embedding-ada-002` | Embedding deployment name |
| `embeddingModelVersion` | `2` | Embedding model version |
| `embeddingModelCapacity` | `120` | Embedding capacity (TPM, thousands) |

---

## Read the outputs

The deployment prints values you'll reuse in the rest of the workshop:

| Output | Use it for |
|--------|-----------|
| `accountName` | The Foundry account name (to fetch endpoint/key in Step 4) |
| `accountEndpoint` | `AZURE_OPENAI_ENDPOINT` for the Movies Tool API |
| `projectEndpoint` | `FOUNDRY_PROJECT_ENDPOINT` for the evaluations in Step 2 (uses the `services.ai.azure.com` host the Azure AI Projects SDK requires) |
| `chatDeploymentName` | The agent model (`gpt-4.1`) |
| `embeddingDeploymentName` | `EMBEDDING_MODEL` for the Movies Tool API (`text-embedding-ada-002`) |

> The account name is **randomly suffixed** (e.g. `foundryab12`). Copy the output values — later
> steps reference this exact name and these endpoints.

Fetch them anytime:

```powershell
az deployment group show `
  --resource-group mongodb-agent-rg `
  --name main `
  --query properties.outputs
```

---

## Verify

Confirm both deployments exist:

```powershell
az cognitiveservices account deployment list `
  --resource-group mongodb-agent-rg `
  --name <accountName-from-output> `
  --query "[].{name:name, model:properties.model.name}" -o table
```

Or in the [Foundry portal](https://ai.azure.com): open project `demo` → **Models + endpoints** →
confirm `gpt-4.1` and `text-embedding-ada-002` show **Succeeded**.

---

## Next

Continue to the base agent: [simple-rag-movies guide](../README.md).

---

## Notes

- **Local auth (keys):** this template sets `disableLocalAuth: false` so the Movies Tool API can call
  Foundry with the `api-key` header. If your policy requires `disableLocalAuth: true`, switch the
  Movies Tool API to Entra ID / managed identity authentication instead of a key.
- **Serial deployments:** Cognitive Services cannot create two model deployments on one account in
  parallel, so the embedding deployment `dependsOn` the chat deployment.
