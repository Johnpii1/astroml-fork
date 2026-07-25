"""NL Query router — natural language query endpoints.

Resolves #457: Exposes structured NL-to-SQL/NL-to-API query capabilities.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.services.llm import LLMService
from api.routers.llm import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm/query", tags=["llm", "query"])


class NLQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, description="Natural language query")
    target: str = Field("sql", pattern="^(sql|api|graphql)$", description="Query target type")
    schema_hint: str | None = Field(None, description="Optional schema context to ground query")
    model: str = Field("gpt-4-turbo")


class NLQueryResponse(BaseModel):
    id: str
    query: str
    target: str
    generated: str = Field(..., description="Generated SQL / API call / GraphQL query")
    explanation: str
    confidence: float
    latency_ms: float


@router.post(
    "/",
    response_model=NLQueryResponse,
    summary="Natural language to structured query",
    operation_id="llm_nl_query",
)
async def nl_query(
    body: NLQueryRequest,
    request: Request,
    service: LLMService = Depends(get_llm_service),
) -> NLQueryResponse:
    """Convert a natural language query into a structured query (SQL, API, GraphQL)."""
    schema_ctx = f"\nSchema context:\n{body.schema_hint}" if body.schema_hint else ""
    prompt = (
        f"Convert the following natural language query to a valid {body.target.upper()} query."
        f"{schema_ctx}\n\nQuery: {body.query}\n\nReturn only the {body.target.upper()} query."
    )
    user_id = getattr(request.state, "user_id", None)
    try:
        result = await service.generate(prompt=prompt, model=body.model, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return NLQueryResponse(
        id=result["id"],
        query=body.query,
        target=body.target,
        generated=result["content"],
        explanation=f"Generated {body.target.upper()} from natural language input.",
        confidence=0.85,
        latency_ms=result["latency_ms"],
    )
