# 🧪 Agent Evaluation — simple-rag-movies

Code-based, **portal-visible** evaluation for the **simple-rag-movies** Foundry agent.

[`run_eval_cloud.py`](run_eval_cloud.py) submits an evaluation to your Foundry project
using the OpenAI-compatible **Evals API** (via `azure-ai-projects`). The agent is
invoked **server-side** for each test query, the responses are graded by Foundry
evaluators, and the run shows up natively under **Build → Evaluations** in the
[Foundry portal](https://ai.azure.com) — with tables, charts, and per-row drill-down.

The headline metric is **`tool_call_accuracy`**: because this agent's whole purpose is to
**query MongoDB**, the eval verifies the agent actually *called the database tools* — not just
that the answer reads well. See [How `tool_call_accuracy` works](#️-how-tool_call_accuracy-works-and-why-tool_definitions-is-required) below.

Based on the official sample:
[Azure/azure-sdk-for-python — sample_agent_evaluation.py](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/sample_agent_evaluation.py)

---

## 📁 Files

```
samples/simple-rag-movies/evals/
├── run_eval_cloud.py   # Submits a portal-visible eval run; also holds the static TOOL_DEFINITIONS
├── dataset.json        # Test queries (structured, aggregation, semantic, no-hallucination)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🧩 What the dataset tests

The dataset exercises the agent's three routing paths plus a guardrail check:

| Category | Example query | What good looks like |
|----------|---------------|----------------------|
| Structured (find) | "Show me movies from 1994" | Calls the `find` tool, returns catalog data |
| Aggregation | "Top 10 highest rated sci-fi movies" | Calls the `aggregate` tool (sort + limit) |
| Semantic (vector) | "Find movies about hope and redemption" | Calls `EmbeddingGenerator`, then `aggregate` with `$vectorSearch` |
| No-hallucination | "Show me movies from 1850" | Reports no results, does NOT invent titles |

Evaluators applied (from the Foundry evaluator catalog):

| Evaluator | Scores | Measures |
|-----------|--------|----------|
| `builtin.tool_call_accuracy` | 1–5 | **Did the agent call the right MongoDB tools, with correct parameters?** This is the headline metric — it verifies the agent actually queried MongoDB rather than answering from the model's memory. |
| `builtin.intent_resolution` | 1–5 | Did the agent understand what the user asked for |
| `builtin.task_adherence` | 1–5 | Did it follow the instructions / do what was asked |
| `builtin.relevance` | 1–5 | Is the answer relevant to the query |
| `builtin.coherence` | 1–5 | Is the answer logically structured |
| `builtin.fluency` | 1–5 | Is the answer well written |

---

## 🛠️ How `tool_call_accuracy` works (and why `tool_definitions` is required)

This is the key evaluator for this sample — **calling MongoDB is the point**, and
`tool_call_accuracy` is what verifies the agent did it.

It needs **two** things wired into the data mapping:

| Field | Mapped to | Why |
|-------|-----------|-----|
| `response` | `{{sample.output_items}}` | The agent's **structured** output — the `openapi_call` / `mcp_call` entries the evaluator parses to see which tools were invoked. (Plain `{{sample.output_text}}` carries no tool calls.) |
| `tool_definitions` | `{{item.tool_definitions}}` | A **static, explicit** list of the tools available to the agent. Each entry must be flat, with a top-level `name`. |

The `TOOL_DEFINITIONS` list lives at the top of [`run_eval_cloud.py`](run_eval_cloud.py) and is
injected into every dataset row. The `name` values **must match the tool-call names the agent
emits**:

| Agent action | Emitted call name |
|--------------|-------------------|
| Direct lookup | `find` |
| Aggregation / vector search | `aggregate` |
| Count | `count` |
| Embedding (semantic) | `EmbeddingGenerator_generateEmbedding` |

> **Note:** because `tool_definitions` is included in the data, the other evaluators that
> accept it (`intent_resolution`, `task_adherence`) also map it. The script already does this.

---

## ✅ Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | `pip install -r requirements.txt` |
| `az login` | Your identity needs **Azure AI Developer** on the Foundry project |
| Grader model deployment | e.g. `gpt-4.1` (used as the LLM judge) |

---

## ▶️ Run it

```powershell
cd samples/simple-rag-movies/evals

# 1. Install dependencies
pip install -r requirements.txt

# 2. Authenticate
az login

# 3. Configure the target
$env:FOUNDRY_PROJECT_ENDPOINT = "https://<account>.services.ai.azure.com/api/projects/<project>"
$env:FOUNDRY_AGENT_NAME       = "mongodb-search-agent"
$env:FOUNDRY_AGENT_VERSIONS   = "<version>"  # e.g. "42"; leave unset for the latest version
$env:FOUNDRY_MODEL_NAME       = "gpt-4.1"     # grader/judge model deployment

# 4. Submit the evaluation
python run_eval_cloud.py
```

The script prints the **eval id** and each **run id**, then polls until completion.

### Compare multiple agent versions

Pass a comma-separated list of versions to evaluate several at once. Each version
becomes its own run under the **same evaluation**, so you can multi-select them in the
portal and compare how each performs against the dataset:

```powershell
$env:FOUNDRY_AGENT_VERSIONS = "40,42"
python run_eval_cloud.py
```

Then in **Build → Evaluations**, open the `simple-rag-movies-eval` evaluation and use
**Select multiple runs to compare results statistically** to view the versions side by side.

### View results

Go to [ai.azure.com](https://ai.azure.com) → your project → **Build → Evaluations** →
open **`simple-rag-movies-eval`**. You'll see per-query scores for every evaluator, plus
charts and drill-down. When you evaluate multiple versions, select all the runs to
compare them statistically — shareable and demo-ready.

---

## 🔧 Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `FOUNDRY_PROJECT_ENDPOINT` | — (required) | `https://<account>.services.ai.azure.com/api/projects/<project>` |
| `FOUNDRY_AGENT_NAME` | `mongodb-search-agent` | Agent to evaluate |
| `FOUNDRY_AGENT_VERSIONS` | latest | Comma-separated versions, e.g. `42` or `40,42` |
| `FOUNDRY_MODEL_NAME` | `gpt-4.1` | LLM judge / grader model deployment |
| `EVAL_RUN_NAME` | `simple-rag-movies-eval` | Display name in the portal |

To change the evaluators or test queries, edit the `build_testing_criteria()` function
in [`run_eval_cloud.py`](run_eval_cloud.py) and the queries in
[`dataset.json`](dataset.json).

> **Note:** evaluate the agent with **memory disabled** so each test query is graded
> independently and runs are reproducible.

---

## 📚 References

- [Agent evaluation sample (azure-ai-projects)](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations)
- [Foundry Observability Concepts](https://learn.microsoft.com/azure/ai-foundry/concepts/observability)
- [Evaluation evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/)
