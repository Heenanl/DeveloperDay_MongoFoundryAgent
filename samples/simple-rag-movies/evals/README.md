# 🧪 Agent Evaluation — simple-rag-movies

Offline evaluation for the **simple-rag-movies** Foundry agent using the
[microsoft/ai-agent-evals](https://github.com/microsoft/ai-agent-evals) GitHub Action.

The action invokes your agent with a set of test queries, runs Foundry evaluators
(model-as-judge + safety + metrics), and posts a summary report to the GitHub
Actions run. When you pass two agent versions it produces a statistical comparison.

---

## 📁 Files

```
samples/simple-rag-movies/evals/
├── dataset.json        # Full eval set (structured, semantic, and "no-hallucination" cases)
├── dataset-tiny.json   # Minimal 3-query smoke test
├── run_eval_local.py   # Local (SDK) evaluation runner — use when CI can't reach private storage
├── requirements.txt    # Python deps for the local runner
└── README.md           # This file

.github/workflows/
└── simple-rag-movies-eval.yml   # CI workflow that runs the action
```

> **Two ways to run:**
> 1. **CI (GitHub Action)** — fully automated, but requires the Foundry project storage to be reachable from the GitHub-hosted runner. If the project uses a **private storage account** (public network disabled), the action's data upload fails with `AuthorizationFailure`. Use the local runner instead.
> 2. **Local (SDK)** — `run_eval_local.py` invokes the agent and scores responses **in-process** on your machine, avoiding the project storage entirely. Recommended for private-agent projects.

---

## 🧩 What the dataset tests

The dataset is designed around the agent's two routing paths plus a guardrail check:

| Category | Example query | What good looks like |
|----------|---------------|----------------------|
| Structured (find) | "Show me movies from 1994" | Calls the find tool, returns catalog data |
| Aggregation | "Top 10 highest rated sci-fi movies" | Calls the aggregate tool (sort + limit) |
| Semantic (vector) | "Find movies about hope and redemption" | Generates an embedding, then vector search |
| No-hallucination | "Show me movies from 1850" | Reports no results, does NOT invent titles |

Evaluators used (from the Foundry evaluator catalog):

- `builtin.intent_resolution` — did the agent understand the request
- `builtin.task_adherence` — did it do what was asked
- `builtin.tool_call_accuracy` — did it call the right tool with valid args
- `builtin.relevance`, `builtin.coherence`, `builtin.fluency` — response quality

> Check the exact evaluator names available to you under **Foundry portal → Build → Evaluations → Evaluator catalog** and adjust `evaluators` in [dataset.json](dataset.json) if needed.

---

## ⚙️ One-time setup

### 1. Configure OIDC (federated credentials) for `azure/login`

The workflow authenticates to Azure with OIDC (no stored secrets). Create an app
registration (or use a user-assigned managed identity) with a **federated credential**
for this GitHub repo, and grant it access to the Foundry project
(e.g. **Azure AI Developer** role on the project/account).

See: [Configure a federated identity credential for GitHub Actions](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect).

### 2. Add GitHub Actions **Variables**

Repo → **Settings → Secrets and variables → Actions → Variables**:

| Variable | Example | Notes |
|----------|---------|-------|
| `AZURE_CLIENT_ID` | `<app-client-id>` | Identity with the federated credential |
| `AZURE_TENANT_ID` | `<tenant-guid>` | Entra ID tenant |
| `AZURE_SUBSCRIPTION_ID` | `<sub-guid>` | Subscription with the Foundry project |
| `FOUNDRY_PROJECT_ENDPOINT` | `https://<account>.services.ai.azure.com/api/projects/<project>` | Foundry project endpoint |
| `EVAL_DEPLOYMENT_NAME` | `gpt-4.1` | Model deployment used to run the evaluators |
| `EVAL_AGENT_IDS` | `mongodb-search-agent:1` | `name:version`; comma-separate two to compare |
| `EVAL_BASELINE_AGENT_ID` | `mongodb-search-agent:1` | *(optional)* Baseline for A/B comparison; leave unset to use the first id in `EVAL_AGENT_IDS` |

> Find the project endpoint in the Foundry portal (project overview) or via
> `az` (CognitiveServices account + project). Find the agent version in the
> agent's header (e.g. "Version: 13").

---

## ▶️ Run it

- **Manually:** Actions tab → **Simple RAG Movies - Agent Evaluation** → **Run workflow**
- **Automatically:** on push to `main` that touches the evals folder or the workflow file

The report (scores, latency, token counts, and pass/fail per evaluator) appears in the
**Actions run summary**.

### Compare two agent versions (A/B)

Set `EVAL_AGENT_IDS` to two comma-separated ids to get a statistical comparison:

```
mongodb-search-agent:1,mongodb-search-agent:2
```

By default the **first** id is the baseline. To pin a specific baseline explicitly,
set the optional `EVAL_BASELINE_AGENT_ID` variable (e.g. `mongodb-search-agent:1`).
Leave it unset for the default behavior.

---

## 🧪 Quick local sanity check (optional)

You can validate the dataset JSON shape before pushing:

```powershell
Get-Content samples/simple-rag-movies/evals/dataset.json | ConvertFrom-Json | Out-Null
Write-Output "dataset.json is valid JSON"
```

---

## �️ Run in the Foundry portal (recommended for demos)

The Foundry portal evaluation runs **server-side inside Azure** and shows the run
natively under **Build → Evaluations** (tables, charts, per-row drill-down). This is
the best option to demo or share with an audience.

### Networking prerequisite

The portal eval uploads results to the **project's storage account**. If that storage
has public network access **Disabled**, the run fails with `AuthorizationFailure`.
Because the Foundry service is a trusted Azure service, you only need public access
enabled **with the firewall still closed to the open internet**:

```powershell
# Minimal, reversible: allow trusted Azure services (Foundry) through; deny the public internet.
az storage account update `
  --name <PROJECT_STORAGE_ACCOUNT> `
  --resource-group <PROJECT_RG> `
  --public-network-access Enabled `
  --default-action Deny `
  --bypass AzureServices

# Revert after the demo:
# az storage account update --name <PROJECT_STORAGE_ACCOUNT> --resource-group <PROJECT_RG> --public-network-access Disabled
```

> The **GitHub Action** route (above) instead needs `--default-action Allow`, because the
> GitHub-hosted runner connects from a public IP and is **not** an Azure service — so the
> `AzureServices` bypass doesn't cover it. The portal route is more secure for demos.

### Steps

1. Convert the dataset to JSONL (Foundry expects one JSON object per line):
   ```powershell
   (Get-Content samples/simple-rag-movies/evals/dataset.json -Raw | ConvertFrom-Json).data |
     ForEach-Object { $_ | ConvertTo-Json -Compress } |
     Set-Content -Path samples/simple-rag-movies/evals/dataset.jsonl -Encoding utf8
   ```
2. Go to [ai.azure.com](https://ai.azure.com) → your project → **Build → Evaluations**.
3. **+ New evaluation** → **Evaluate an agent**.
4. Select **mongodb-search-agent** → the working **version**.
5. **Upload dataset** → `dataset.jsonl`; map the `query` column as the input.
6. Pick evaluators: Intent resolution, Task adherence, Tool call accuracy, Relevance,
   Coherence, Fluency.
7. Grader model: **gpt-4.1** → **Run**.
8. Results appear under **Build → Evaluations** — shareable and demo-ready.

> `Tool call accuracy` scores correctly here because the portal extracts the agent's
> tool calls automatically (the local runner can't, so it shows ERR for that one metric).

---

## �💻 Run locally with the SDK (recommended for private-agent projects)

If your Foundry project uses a **private storage account** (the CI action fails with
`AuthorizationFailure` / `ResourceMsiTokenDoesntHavePermissionsOnStorage`), run the
evaluators locally instead. The local runner invokes the agent and scores responses
in-process, so it never touches the project storage.

```powershell
cd samples/simple-rag-movies/evals

# 1. Install dependencies (Python 3.10–3.12 recommended)
pip install -r requirements.txt

# 2. Authenticate (DefaultAzureCredential)
az login

# 3. Configure the target (or put these in a .env file)
$env:FOUNDRY_PROJECT_ENDPOINT = "https://aiservicesktdp.services.ai.azure.com/api/projects/Mongodb-demo"
$env:EVAL_AGENT_NAME = "mongodb-search-agent"
$env:EVAL_AGENT_VERSION = "26"
$env:EVAL_MODEL_DEPLOYMENT = "gpt-4.1"

# 4. Run
python run_eval_local.py
```

Outputs a per-query console summary and writes detailed scores to `eval-results.json`.

> Requires that your signed-in identity has **Azure AI Developer** on the project.
> The model-graded evaluators call the `EVAL_MODEL_DEPLOYMENT` model as the judge.

---

## 🔧 Customizing

- **Smaller/faster run:** point `data-path` at `dataset-tiny.json` in the workflow.
- **More evaluators:** add names from your evaluator catalog to the `evaluators` array.
- **Custom / OpenAI graders:** see the action's
  [sample data files](https://github.com/microsoft/ai-agent-evals/tree/main/samples/data)
  for `openai_graders`, `evaluator_parameters`, and `data_mapping` examples.

---

## 📚 References

- [microsoft/ai-agent-evals (Marketplace action)](https://github.com/microsoft/ai-agent-evals)
- [Foundry Observability Concepts](https://learn.microsoft.com/azure/ai-foundry/concepts/observability)
- [Evaluation evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/)
