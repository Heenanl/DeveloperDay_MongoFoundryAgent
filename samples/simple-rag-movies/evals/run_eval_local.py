"""
Local agent evaluation for the simple-rag-movies Foundry agent.

Runs the agent against the test queries in dataset.json, then scores each
response with Foundry evaluators LOCALLY (in-process). Running locally avoids
the project's private storage account, which blocks the GitHub-hosted CI runner.

Usage:
    # 1. Configure a Python environment and install deps
    pip install -r requirements.txt

    # 2. Authenticate (uses DefaultAzureCredential -> `az login` works)
    az login

    # 3. Set the project endpoint + agent (or use a .env file)
    setx FOUNDRY_PROJECT_ENDPOINT "https://<account>.services.ai.azure.com/api/projects/<project>"
    setx EVAL_AGENT_NAME "mongodb-search-agent"
    setx EVAL_AGENT_VERSION "26"
    setx EVAL_MODEL_DEPLOYMENT "gpt-4.1"

    # 4. Run
    python run_eval_local.py

Outputs a per-query table and writes results to eval-results.json.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Foundry built-in evaluators (run locally)
from azure.ai.evaluation import (
    IntentResolutionEvaluator,
    TaskAdherenceEvaluator,
    ToolCallAccuracyEvaluator,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
)

load_dotenv(override=True)

HERE = Path(__file__).parent
DATASET = HERE / "dataset.json"
RESULTS = HERE / "eval-results.json"

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
AGENT_NAME = os.environ.get("EVAL_AGENT_NAME", "mongodb-search-agent")
AGENT_VERSION = os.environ.get("EVAL_AGENT_VERSION", "26")
MODEL_DEPLOYMENT = os.environ.get("EVAL_MODEL_DEPLOYMENT", "gpt-4.1")


def build_evaluators(project_endpoint: str, model_deployment: str) -> dict:
    """Create the evaluator instances. Model-graded evaluators need a judge model."""
    model_config = {
        "azure_endpoint": project_endpoint.split("/api/projects/")[0],
        "azure_deployment": model_deployment,
    }
    return {
        "intent_resolution": IntentResolutionEvaluator(model_config=model_config),
        "task_adherence": TaskAdherenceEvaluator(model_config=model_config),
        "tool_call_accuracy": ToolCallAccuracyEvaluator(model_config=model_config),
        "relevance": RelevanceEvaluator(model_config=model_config),
        "coherence": CoherenceEvaluator(model_config=model_config),
        "fluency": FluencyEvaluator(model_config=model_config),
    }


def run_agent(project_client: AIProjectClient, query: str) -> dict:
    """Invoke the agent with a single query and return the response + tool calls."""
    openai_client = project_client.get_openai_client()
    conversation = openai_client.conversations.create(
        items=[{"type": "message", "role": "user", "content": query}]
    )
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={
            "agent_reference": {
                "name": AGENT_NAME,
                "type": "agent_reference",
                "version": AGENT_VERSION,
            }
        },
        input="",
    )
    return {
        "response": getattr(response, "output_text", str(response)),
        "raw": response,
    }


def main() -> None:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    queries = data["data"]

    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)
    evaluators = build_evaluators(PROJECT_ENDPOINT, MODEL_DEPLOYMENT)

    results = []
    print(f"Evaluating {len(queries)} queries against {AGENT_NAME}:{AGENT_VERSION}\n")

    with project_client:
        for i, item in enumerate(queries, 1):
            query = item["query"]
            ground_truth = item.get("ground_truth", "")
            print(f"[{i}/{len(queries)}] {query}")

            try:
                agent_out = run_agent(project_client, query)
                answer = agent_out["response"]
            except Exception as e:  # noqa: BLE001
                print(f"    agent error: {e}")
                results.append({"query": query, "error": str(e)})
                continue

            scores = {}
            for name, evaluator in evaluators.items():
                try:
                    eval_kwargs = {"query": query, "response": answer}
                    if ground_truth and name in ("relevance",):
                        eval_kwargs["ground_truth"] = ground_truth
                    scores[name] = evaluator(**eval_kwargs)
                except Exception as e:  # noqa: BLE001
                    scores[name] = {"error": str(e)}

            results.append(
                {"query": query, "response": answer, "scores": scores}
            )
            # Brief console summary
            summary = ", ".join(
                f"{k}={v.get(k) if isinstance(v, dict) else v}"
                for k, v in scores.items()
            )
            print(f"    {summary}\n")

    RESULTS.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Wrote detailed results to {RESULTS}")


if __name__ == "__main__":
    main()
