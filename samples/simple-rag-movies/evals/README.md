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
└── README.md           # This file

.github/workflows/
└── simple-rag-movies-eval.yml   # CI workflow that runs the action
```

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
