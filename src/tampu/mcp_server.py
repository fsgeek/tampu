from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ToolAnnotations
from pydantic import SkipValidation

from .config import load_config
from .repository import Repository
from .service import Service, compact_json


def _content(value: dict) -> TextContent:
    return TextContent(type="text", text=compact_json(value))


def create_server(service: Service) -> FastMCP:
    server = FastMCP(
        "Tampu",
        instructions=(
            "Investigate only published, revision-pinned PDF collection state through "
            "four bounded tools. Handles and continuations are process-local and opaque."
        ),
        log_level="ERROR",
    )

    @server.tool(
        name="describe",
        description=(
            "Describe published collections and paged published revision IDs, bounded "
            "facets, supported filter keys/examples, extraction coverage/losses, projection "
            "recipes, lexical any_terms/all_terms/phrase modes, limits, and honestly "
            "unavailable capabilities. Detail is paged. This is a durable read-only "
            "operation."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=False,
    )
    def describe(
        collection: SkipValidation[str | None] = None,
        cursor: SkipValidation[str | None] = None,
        limit: SkipValidation[int] = 10,
        facet: SkipValidation[str | None] = None,
        facet_cursor: SkipValidation[str | None] = None,
        detail_limit: SkipValidation[int] = 20,
        revision_cursor: SkipValidation[str | None] = None,
        revision_limit: SkipValidation[int] = 2,
        byte_budget: SkipValidation[int] = 8192,
    ) -> TextContent:
        return _content(
            service.describe(
                collection=collection,
                cursor=cursor,
                limit=limit,
                facet=facet,
                facet_cursor=facet_cursor,
                detail_limit=detail_limit,
                revision_cursor=revision_cursor,
                revision_limit=revision_limit,
                byte_budget=byte_budget,
            )
        )

    @server.tool(
        name="search",
        description=(
            "Start a finding journey with collection and intent, or reuse journey_id with "
            "a new predicate. The first call creates a pinned revision and projection "
            "selection. lexical/v1 requires query plus any_terms, all_terms, or phrase; "
            "metadata/v1 and temporal/v1 require an empty query, mode=filter, and typed "
            "filters. limit=0 is an exact count-only request; limits 1..20 return bounded "
            "hits and an opaque continuation. This reads durable data and writes only "
            "expiring process-local journey state."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=False,
    )
    def search(
        collection: SkipValidation[str | None] = None,
        revision: SkipValidation[str | None] = None,
        intent: SkipValidation[str | None] = None,
        journey_id: SkipValidation[str | None] = None,
        lens: SkipValidation[str] = "lexical/v1",
        query: SkipValidation[str] = "",
        mode: SkipValidation[str] = "any_terms",
        filters: SkipValidation[dict[str, Any] | None] = None,
        limit: SkipValidation[int] = 2,
        byte_budget: SkipValidation[int] = 8192,
    ) -> TextContent:
        return _content(
            service.search(
                collection=collection,
                revision=revision,
                intent=intent,
                journey_id=journey_id,
                lens=lens,
                query=query,
                mode=mode,
                filters=filters,
                limit=limit,
                byte_budget=byte_budget,
            )
        )

    @server.tool(
        name="inspect",
        description=(
            "Page a node's candidates, or open bounded metadata/evidence from any artifact "
            "in that node, including an unseen candidate, by artifact_id plus physical PDF "
            "page or element ordinal. Then slice text with its opaque evidence handle; "
            "continuations preserve Unicode character boundaries. Physical PDF pages are "
            "distinct from unknown printed-page labels. This reads durable data and writes "
            "only expiring process-local delivery/inspection state."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=False,
    )
    def inspect(
        journey_id: SkipValidation[str | None] = None,
        node_id: SkipValidation[str | None] = None,
        continuation: SkipValidation[str | None] = None,
        limit: SkipValidation[int] = 2,
        evidence_handle: SkipValidation[str | None] = None,
        artifact_id: SkipValidation[str | None] = None,
        ordinal: SkipValidation[int | None] = None,
        page: SkipValidation[int | None] = None,
        start: SkipValidation[int | None] = None,
        end: SkipValidation[int | None] = None,
        slice_chars: SkipValidation[int] = 800,
        byte_budget: SkipValidation[int] = 8192,
    ) -> TextContent:
        return _content(
            service.inspect(
                journey_id=journey_id,
                node_id=node_id,
                continuation=continuation,
                limit=limit,
                evidence_handle=evidence_handle,
                artifact_id=artifact_id,
                ordinal=ordinal,
                page=page,
                start=start,
                end=end,
                slice_chars=slice_chars,
                byte_budget=byte_budget,
            )
        )

    @server.tool(
        name="finish",
        description=(
            "Record a process-local positive, bounded_negative, or unresolved finding. "
            "Positive findings require successfully inspected opaque evidence handles; "
            "bounded_negative requires an exact zero-candidate node and does not prove "
            "semantic absence; unresolved requires a reason. release=true destructively "
            "frees the active journey without a preservation claim. Trace persistence "
            "occurs only when the owner explicitly started serve with --trace."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=False,
    )
    def finish(
        journey_id: SkipValidation[str | None] = None,
        kind: SkipValidation[str | None] = None,
        statement: SkipValidation[str | None] = None,
        evidence_handles: SkipValidation[list[str] | None] = None,
        node_id: SkipValidation[str | None] = None,
        reason: SkipValidation[str | None] = None,
        semantic_absence: SkipValidation[bool] = False,
        release: SkipValidation[bool] = False,
        byte_budget: SkipValidation[int] = 8192,
    ) -> TextContent:
        return _content(
            service.finish(
                journey_id=journey_id,
                kind=kind,
                statement=statement,
                evidence_handles=evidence_handles,
                node_id=node_id,
                reason=reason,
                semantic_absence=semantic_absence,
                release=release,
                byte_budget=byte_budget,
            )
        )

    required = {
        "inspect": ("journey_id", "node_id"),
        "finish": ("journey_id", "kind", "statement"),
    }
    for name, fields in required.items():
        tool = server._tool_manager.get_tool(name)
        if tool is None:  # pragma: no cover - registration above is deterministic
            raise RuntimeError("Tampu tool registration failed")
        tool.parameters["required"] = list(fields)
        for field in fields:
            tool.parameters["properties"][field] = {
                "title": field.replace("_", " ").title(),
                "type": "string",
            }

    return server


def run_server(*, trace_path: Path | None = None) -> None:
    operations = logging.getLogger("tampu.operations")
    if not operations.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        operations.addHandler(handler)
    operations.setLevel(logging.INFO)
    operations.propagate = False
    repository = Repository(load_config(), initialize=False)
    create_server(Service(repository, trace_path=trace_path)).run(transport="stdio")
