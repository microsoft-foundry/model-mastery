# SPDX-License-Identifier: MIT
# Portions Copyright (c) 2026 Shilpa Jain
# Derived from https://github.com/ShilJain/Claude-on-foundry-handsonworkshop
"""Build the Sparkles knowledge base in Foundry IQ (instructors run this once).

Foundry IQ is the managed knowledge layer in Microsoft Foundry, built on
Azure AI Search. This script:

  1. Creates a search index with a semantic configuration.
  2. Chunks docs/cupcake-store-info.md by section and uploads the chunks.
  3. Creates a knowledge source over that index.
  4. Creates a knowledge base that references the knowledge source, with
     retrieval reasoning effort set to MINIMAL and extractive output. The
     knowledge base only returns matching passages: no query planning, no
     answer synthesis, and no model deployment of its own. Claude does the
     reasoning in the agent.

The knowledge base then exposes an MCP endpoint that the Sparkles agent uses
as a second tool (Lab 1, Module 1.3).

Required in .env:
  AZURE_SEARCH_ENDPOINT     https://<service>.search.windows.net
  AZURE_SEARCH_ADMIN_KEY    admin key (leave empty to use Entra ID login)
Optional:
  KNOWLEDGE_BASE_NAME       default cupcake-store-kb

Run:  pip install -r requirements.txt && python ingest_foundry_iq.py
"""

import os
import re
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeRetrievalMinimalReasoningEffort,
)
from azure.search.documents.indexes.models import (
    KnowledgeBase,
    KnowledgeSourceReference,
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
)
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

DOCUMENT_PATH = HERE / "docs" / "cupcake-store-info.md"
KNOWLEDGE_BASE_NAME = os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")
INDEX_NAME = f"{KNOWLEDGE_BASE_NAME}-index"
KNOWLEDGE_SOURCE_NAME = f"{KNOWLEDGE_BASE_NAME}-source"
SEMANTIC_CONFIG_NAME = "cupcake-semantic"
# The SDK's default API version. The MCP URL the agent uses must match it.
API_VERSION = "2026-08-01-preview"


def credential():
    key = os.environ.get("AZURE_SEARCH_ADMIN_KEY")
    return AzureKeyCredential(key) if key else DefaultAzureCredential()


def chunk_document(path: Path) -> list[dict]:
    """One chunk per level-2 section, heading kept with its body."""
    parts = re.split(r"\n(?=## )", path.read_text(encoding="utf-8"))
    chunks = []
    for i, part in enumerate(parts):
        body = part.strip()
        if not body:
            continue
        heading = body.splitlines()[0].lstrip("# ").strip()
        chunks.append({"id": str(i), "title": heading, "category": heading, "content": body})
    return chunks


def main() -> None:
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    cred = credential()
    index_client = SearchIndexClient(endpoint=endpoint, credential=cred, api_version=API_VERSION)

    chunks = chunk_document(DOCUMENT_PATH)
    print(f"Prepared {len(chunks)} chunks from {DOCUMENT_PATH.name}")

    index_client.create_or_update_index(SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String,
                            filterable=True, facetable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
        ],
        semantic_search=SemanticSearch(configurations=[SemanticConfiguration(
            name=SEMANTIC_CONFIG_NAME,
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")],
            ),
        )]),
    ))
    print(f"Index {INDEX_NAME} created or updated")

    result = SearchClient(endpoint=endpoint, index_name=INDEX_NAME,
                          credential=cred).upload_documents(documents=chunks)
    print(f"Uploaded {sum(1 for r in result if r.succeeded)}/{len(chunks)} chunks")

    index_client.create_or_update_knowledge_source(SearchIndexKnowledgeSource(
        name=KNOWLEDGE_SOURCE_NAME,
        description="Sparkles store information: hours, delivery, returns, allergens, loyalty, bulk orders.",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=INDEX_NAME,
            semantic_configuration_name=SEMANTIC_CONFIG_NAME,
            source_data_fields=[SearchIndexFieldReference(name=n)
                                for n in ("id", "title", "category", "content")],
            search_fields=[SearchIndexFieldReference(name="content")],
        ),
    ))
    print(f"Knowledge source {KNOWLEDGE_SOURCE_NAME} created or updated")

    index_client.create_or_update_knowledge_base(KnowledgeBase(
        name=KNOWLEDGE_BASE_NAME,
        description="Foundry IQ knowledge base for the Sparkles cupcake shop.",
        knowledge_sources=[KnowledgeSourceReference(name=KNOWLEDGE_SOURCE_NAME)],
        # Without these two settings the service defaults to "low" effort,
        # which plans queries with a model deployment this knowledge base
        # does not have.
        retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
        output_mode="extractiveData",
    ))
    kb = index_client.get_knowledge_base(KNOWLEDGE_BASE_NAME)
    # 12.1.0b2 reads the effort back as a plain dict, not a model object.
    effort = kb.retrieval_reasoning_effort
    kind = effort.get("kind") if isinstance(effort, dict) else getattr(effort, "kind", None)
    print(f"  reasoning effort: {kind}  output: {kb.output_mode}")
    assert kind == "minimal", "reasoning effort was not applied"
    assert kb.output_mode == "extractiveData", "output mode was not applied"
    print(f"Knowledge base {KNOWLEDGE_BASE_NAME} created or updated")
    print(f"\nMCP endpoint for the agent:\n"
          f"  {endpoint}/knowledgebases/{KNOWLEDGE_BASE_NAME}/mcp?api-version={API_VERSION}")


if __name__ == "__main__":
    main()
