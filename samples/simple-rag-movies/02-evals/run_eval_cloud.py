"""
Cloud (portal-visible) agent evaluation for the simple-rag-movies Foundry agent.

Submits an evaluation to the Foundry project using the OpenAI-compatible Evals API
(via `project_client.get_openai_client()`). Runs appear in the Foundry portal under
**Build -> Evaluations** — shareable and demo-ready.

You can evaluate ONE version or SEVERAL versions in a single invocation. When you pass
multiple versions, each becomes its own run under the **same evaluation**, so you can
multi-select them in the portal and compare how each version performs on the dataset.

Based on the official sample:
https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/sample_agent_evaluation.py

Requirements:
- azure-ai-projects>=2.0.0 (installed via requirements.txt)
- Your signed-in identity needs **Azure AI Developer** on the project (`az login`).
- The project's storage account must be reachable by the Foundry service
  (public network access Enabled is sufficient; keep firewall on
  defaultAction=Deny + bypass=AzureServices so only Azure services pass).

Usage (PowerShell):
    az login
    $env:FOUNDRY_PROJECT_ENDPOINT = "https://<account>.services.ai.azure.com/api/projects/<project>"
    $env:FOUNDRY_AGENT_NAME       = "mongodb-search-agent"
    $env:FOUNDRY_MODEL_NAME       = "gpt-4.1"        # grader/judge model deployment

    # Single version (or leave unset for the latest):
    $env:FOUNDRY_AGENT_VERSIONS   = "33"

    # Compare multiple versions in one run:
    # $env:FOUNDRY_AGENT_VERSIONS = "31,32,33"

    python run_eval_cloud.py
"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai.types.evals.create_eval_completions_run_data_source_param import (
    SourceFileContent,
    SourceFileContentContent,
)
from openai.types.eval_create_params import DataSourceConfigCustom
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    TestingCriterionAzureAIEvaluator,
    TargetCompletionEvalRunDataSource,
    AzureAIAgentTargetParam,
)

load_dotenv(override=True)

HERE = Path(__file__).parent
DATASET = HERE / "dataset.json"

ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "mongodb-search-agent")
MODEL_NAME = os.environ.get("FOUNDRY_MODEL_NAME", "gpt-4.1")
EVAL_NAME = os.environ.get("EVAL_RUN_NAME", "simple-rag-movies-eval")

# Comma-separated list of agent versions to evaluate. Empty -> latest version.
# Examples: "33"  or  "31,32,33"
_versions_raw = os.environ.get("FOUNDRY_AGENT_VERSIONS", "").strip()
AGENT_VERSIONS = [v.strip() for v in _versions_raw.split(",") if v.strip()] or [None]

# Tool definitions for the tool_call_accuracy evaluator.
#
# This evaluator REQUIRES an explicit `tool_definitions` list — it cannot be
# derived from the agent's runtime output (mapping it to {{sample.output_items}}
# fails with "Each tool definitions must contain a 'name' field"). Each entry must
# be flat: top-level `name`, `description`, `parameters`. The `name` values MUST
# match the tool-call names the agent actually emits, confirmed by probing v33:
#   - direct lookups  -> mcp_call name="find"
#   - aggregations    -> mcp_call name="aggregate"
#   - semantic search -> openapi_call name="EmbeddingGenerator_generateEmbedding"
#                        followed by mcp_call name="aggregate" ($vectorSearch)
TOOL_DEFINITIONS = [
    {
        "name": "find",
        "description": "Run a MongoDB find query against a collection to retrieve "
        "documents matching a filter (used for direct lookups by known fields such "
        "as year, cast, genres, or rating).",
        "parameters": {
            "type": "object",
            "properties": {
                "database": {"type": "string", "description": "Database name, e.g. sample_mflix."},
                "collection": {"type": "string", "description": "Collection name, e.g. movies."},
                "filter": {"type": "object", "description": "MongoDB query filter document."},
                "projection": {"type": "object", "description": "Fields to include or exclude."},
                "limit": {"type": "integer", "description": "Maximum number of documents to return."},
            },
            "required": ["database", "collection"],
        },
    },
    {
        "name": "aggregate",
        "description": "Run a MongoDB aggregation pipeline against a collection. Used for "
        "grouping, sorting, statistics, and for $vectorSearch semantic queries over the "
        "embedded_movies collection.",
        "parameters": {
            "type": "object",
            "properties": {
                "database": {"type": "string", "description": "Database name, e.g. sample_mflix."},
                "collection": {"type": "string", "description": "Collection name, e.g. movies or embedded_movies."},
                "pipeline": {
                    "type": "array",
                    "description": "Ordered list of aggregation stages (e.g. $match, $sort, $limit, $group, $vectorSearch).",
                    "items": {"type": "object"},
                },
            },
            "required": ["database", "collection", "pipeline"],
        },
    },
    {
        "name": "count",
        "description": "Count the number of documents in a collection that match a filter.",
        "parameters": {
            "type": "object",
            "properties": {
                "database": {"type": "string", "description": "Database name, e.g. sample_mflix."},
                "collection": {"type": "string", "description": "Collection name, e.g. movies."},
                "filter": {"type": "object", "description": "MongoDB query filter document."},
            },
            "required": ["database", "collection"],
        },
    },
    {
        "name": "EmbeddingGenerator_generateEmbedding",
        "description": "Generate a 1536-dimension text embedding vector for a search concept. "
        "Called before $vectorSearch for semantic/thematic queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text/concept to embed."},
            },
            "required": ["text"],
        },
    },
]


def build_testing_criteria(model_deployment: str):
    """Evaluators to apply. Model-graded ones take the judge model in init params."""
    return [
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="intent_resolution",
            evaluator_name="builtin.intent_resolution",
            initialization_parameters={"model": model_deployment},
            data_mapping={
                "query": "{{item.query}}",
                "response": "{{sample.output_items}}",
                "tool_definitions": "{{item.tool_definitions}}",
            },
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="task_adherence",
            evaluator_name="builtin.task_adherence",
            initialization_parameters={"model": model_deployment},
            data_mapping={
                "query": "{{item.query}}",
                "response": "{{sample.output_items}}",
                "tool_definitions": "{{item.tool_definitions}}",
            },
        ),
        # Tool Call Accuracy.
        #   response         -> {{sample.output_items}} : the agent's STRUCTURED output
        #                       (openapi_call / mcp_call entries) so the evaluator can
        #                       parse the tool_calls actually made. A memory-only answer
        #                       has NO such entries and therefore cannot score a pass.
        #   tool_definitions -> {{item.tool_definitions}} : the explicit, flat-format
        #                       tool list injected per row (see TOOL_DEFINITIONS). This
        #                       field is REQUIRED and cannot be derived from output_items.
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="tool_call_accuracy",
            evaluator_name="builtin.tool_call_accuracy",
            initialization_parameters={"model": model_deployment},
            data_mapping={
                "query": "{{item.query}}",
                "response": "{{sample.output_items}}",
                "tool_definitions": "{{item.tool_definitions}}",
            },
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="relevance",
            evaluator_name="builtin.relevance",
            initialization_parameters={"model": model_deployment},
            data_mapping={"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="coherence",
            evaluator_name="builtin.coherence",
            initialization_parameters={"model": model_deployment},
            data_mapping={"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="fluency",
            evaluator_name="builtin.fluency",
            initialization_parameters={"model": model_deployment},
            data_mapping={"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        ),
    ]


def build_data_source(queries, version):
    """Build the run data source that targets a specific agent version."""
    target_kwargs = {"type": "azure_ai_agent", "name": AGENT_NAME}
    if version:
        target_kwargs["version"] = version

    return TargetCompletionEvalRunDataSource(
        type="azure_ai_target_completions",
        source=SourceFileContent(
            type="file_content",
            content=[
                SourceFileContentContent(
                    item={"query": q["query"], "tool_definitions": TOOL_DEFINITIONS}
                )
                for q in queries
            ],
        ),
        input_messages={
            "type": "template",
            "template": [
                {
                    "type": "message",
                    "role": "user",
                    "content": {"type": "input_text", "text": "{{item.query}}"},
                }
            ],
        },
        target=AzureAIAgentTargetParam(**target_kwargs),
    )


def main() -> None:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    queries = data["data"]

    versions_label = ", ".join(v or "latest" for v in AGENT_VERSIONS)
    print(f"Agent     : {AGENT_NAME}")
    print(f"Versions  : {versions_label}")
    print(f"Grader    : {MODEL_NAME}")
    print(f"Queries   : {len(queries)}")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=ENDPOINT, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        # One eval definition (schema + evaluators); all version runs attach to it
        # so the portal groups them together for comparison.
        data_source_config = DataSourceConfigCustom(
            type="custom",
            item_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "tool_definitions": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["query"],
            },
            include_sample_schema=True,
        )
        eval_object = openai_client.evals.create(
            name=EVAL_NAME,
            data_source_config=data_source_config,
            testing_criteria=build_testing_criteria(MODEL_NAME),
        )
        print(f"\nEvaluation created (id: {eval_object.id}, name: {eval_object.name})")

        # Create one run per requested agent version.
        runs = []
        for version in AGENT_VERSIONS:
            label = version or "latest"
            run = openai_client.evals.runs.create(
                eval_id=eval_object.id,
                name=f"{AGENT_NAME}:{label}",
                data_source=build_data_source(queries, version),  # type: ignore[arg-type]
            )
            print(f"  + run created for {AGENT_NAME}:{label} (id: {run.id})")
            runs.append(run)

        print("\nView in Foundry portal -> Build -> Evaluations")
        if len(runs) > 1:
            print("Select all the runs in the portal to compare versions side by side.")

        # Poll all runs to completion.
        pending = {r.id for r in runs}
        while pending:
            time.sleep(10)
            for r in runs:
                if r.id not in pending:
                    continue
                latest = openai_client.evals.runs.retrieve(run_id=r.id, eval_id=eval_object.id)
                if latest.status in ("completed", "failed"):
                    pending.discard(r.id)
                    print(f"  {r.name}: {latest.status} "
                          f"(counts: {getattr(latest, 'result_counts', None)})")
                else:
                    print(f"  {r.name}: {latest.status}")

        print("\nDone.")


if __name__ == "__main__":
    main()
