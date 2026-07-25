"""LLM API Gateway router — unified REST endpoints for all LLM features.

Resolves #457: Production-ready LLM API with rate limiting, authentication,
streaming, and comprehensive OpenAPI documentation.

Endpoints:
  POST /api/v1/llm/generate          — Text completion
  POST /api/v1/llm/generate/stream   — Streaming completion (SSE)
  POST /api/v1/llm/embed             — Embeddings
  POST /api/v1/llm/chat              — Chat completion
  POST /api/v1/llm/rag/query         — RAG query
  GET  /api/v1/llm/models            — List available models
  GET  /api/v1/llm/cost/usage        — Cost usage report
  WS   /api/v1/llm/chat/ws           — Streaming chat over WebSocket
  WS   /api/v1/llm/stream            — Generic streaming over WebSocket
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse

from api.schemas.llm import (
    GenerateRequest,
    GenerateResponse,
    EmbedRequest,
    EmbedResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage as SchemaChatMessage,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGDocument,
    ModelsListResponse,
    ModelInfo,
    CostUsageResponse,
    UsageInfo,
    StreamChunk,
    ErrorResponse,
    ErrorDetail,
)
from api.services.llm import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

# Shared service instance (dependency-injectable for testing)
_llm_service = LLMService()


def get_llm_service() -> LLMService:
    return _llm_service


def _get_user_id(request: Request) -> str | None:
    """Extract user ID from request state (set by AuthMiddleware)."""
    return getattr(request.state, "user_id", None)


# ─── REST: Generate ─────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    summary="Generate a text completion",
    operation_id="llm_generate",
)
async def generate_completion(
    body: GenerateRequest,
    request: Request,
    service: LLMService = Depends(get_llm_service),
) -> GenerateResponse:
    """Generate an LLM completion from a prompt.

    Enforces safety guardrails, rate limits, and logs to the audit trail.
    """
    user_id = _get_user_id(request)
    try:
        result = await service.generate(
            prompt=body.prompt,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            user_id=user_id,
            idempotency_key=body.idempotency_key,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GenerateResponse(
        id=result["id"],
        model=result["model"],
        content=result["content"],
        usage=UsageInfo(**result["usage"]),
        cost=result["cost"],
        latency_ms=result["latency_ms"],
        cached=result.get("cached", False),
    )


@router.post(
    "/generate/stream",
    response_class=StreamingResponse,
    summary="Stream a text completion (Server-Sent Events)",
    operation_id="llm_generate_stream",
)
async def generate_stream(
    body: GenerateRequest,
    request: Request,
    service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """Stream an LLM completion as Server-Sent Events."""
    user_id = _get_user_id(request)

    async def _event_generator():
        try:
            async for chunk in service.generate_stream(
                prompt=body.prompt,
                model=body.model,
                user_id=user_id,
            ):
                data = json.dumps({"delta": chunk, "finish_reason": None})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as exc:
            err = json.dumps({"error": str(exc)})
            yield f"data: {err}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── REST: Embed ─────────────────────────────────────────────────────────────

@router.post(
    "/embed",
    response_model=EmbedResponse,
    summary="Generate text embeddings",
    operation_id="llm_embed",
)
async def generate_embeddings(
    body: EmbedRequest,
    service: LLMService = Depends(get_llm_service),
) -> EmbedResponse:
    """Generate vector embeddings for text or a list of texts."""
    texts = [body.input] if isinstance(body.input, str) else body.input
    embeddings = service.embed(texts, model=body.model)
    total_tokens = sum(len(t) // 4 for t in texts)
    return EmbedResponse(
        model=body.model,
        embeddings=embeddings,
        usage=UsageInfo(prompt_tokens=total_tokens, total_tokens=total_tokens),
    )


# ─── REST: Chat ───────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Chat completion",
    operation_id="llm_chat",
)
async def chat_completion(
    body: ChatRequest,
    request: Request,
    service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """Chat completion with a messages list. Supports GPT-style message arrays."""
    user_id = _get_user_id(request)
    try:
        result = await service.chat(
            messages=[m.model_dump() for m in body.messages],
            model=body.model,
            user_id=user_id,
            idempotency_key=body.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ChatResponse(
        id=result["id"],
        model=result["model"],
        message=SchemaChatMessage(role="assistant", content=result["content"]),
        usage=UsageInfo(**result["usage"]),
        cost=result["cost"],
        latency_ms=result["latency_ms"],
    )


# ─── REST: RAG Query ──────────────────────────────────────────────────────────

@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
    summary="RAG-augmented query",
    operation_id="llm_rag_query",
)
async def rag_query(
    body: RAGQueryRequest,
    request: Request,
    service: LLMService = Depends(get_llm_service),
) -> RAGQueryResponse:
    """Retrieve relevant documents then generate a grounded answer."""
    user_id = _get_user_id(request)
    result = await service.rag_query(
        query=body.query,
        top_k=body.top_k,
        model=body.model,
        user_id=user_id,
    )
    return RAGQueryResponse(
        id=result["id"],
        query=result["query"],
        answer=result["answer"],
        documents=[RAGDocument(**d) for d in result["documents"]],
        usage=UsageInfo(**result["usage"]),
        cost=result.get("cost", 0.0),
        latency_ms=result.get("latency_ms", 0.0),
    )


# ─── REST: Models list ────────────────────────────────────────────────────────

@router.get(
    "/models",
    response_model=ModelsListResponse,
    summary="List available LLM models",
    operation_id="llm_list_models",
)
async def list_models(
    service: LLMService = Depends(get_llm_service),
) -> ModelsListResponse:
    """Return all available LLM model definitions with pricing and capabilities."""
    models = service.list_models()
    return ModelsListResponse(
        models=[ModelInfo(**m) for m in models],
        total=len(models),
    )


# ─── REST: Cost usage ────────────────────────────────────────────────────────

@router.get(
    "/cost/usage",
    response_model=CostUsageResponse,
    summary="Get LLM cost usage for the current user",
    operation_id="llm_cost_usage",
)
async def cost_usage(
    request: Request,
    period: str | None = Query(None, description="e.g. '2026-07'"),
    service: LLMService = Depends(get_llm_service),
) -> CostUsageResponse:
    """Return cost and token usage summary for the authenticated user."""
    user_id = _get_user_id(request) or "anonymous"
    report = service.cost_usage(user_id=user_id, period=period)
    return CostUsageResponse(
        user_id=user_id,
        period=report.get("period", "all-time"),
        total_requests=report.get("total_requests", 0),
        total_tokens=report.get("total_tokens", 0),
        total_cost_usd=report.get("total_cost_usd", 0.0),
        cost_by_model=report.get("cost_by_model", {}),
        cost_by_day=report.get("cost_by_day", []),
    )


# ─── WebSocket: Streaming chat ───────────────────────────────────────────────

@router.websocket("/chat/ws")
async def websocket_chat(
    websocket: WebSocket,
    service: LLMService = Depends(get_llm_service),
) -> None:
    """Streaming chat over WebSocket.

    Client sends: ``{"messages": [...], "model": "gpt-4-turbo"}``
    Server streams: ``{"delta": "...", "finish_reason": null}`` chunks
    then: ``{"delta": "", "finish_reason": "stop"}``
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            messages = data.get("messages", [])
            model = data.get("model", "gpt-4-turbo")
            last_user = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "user"),
                "",
            )

            try:
                async for chunk in service.generate_stream(
                    prompt=last_user, model=model
                ):
                    await websocket.send_json({"delta": chunk, "finish_reason": None})
                await websocket.send_json({"delta": "", "finish_reason": "stop"})
            except ValueError as exc:
                await websocket.send_json({"error": str(exc)})

    except WebSocketDisconnect:
        logger.debug("WebSocket chat client disconnected")


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    service: LLMService = Depends(get_llm_service),
) -> None:
    """Generic streaming WebSocket endpoint.

    Client sends: ``{"prompt": "...", "model": "gpt-4-turbo"}``
    Server streams token chunks then sends finish marker.
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            prompt = data.get("prompt", "")
            model = data.get("model", "gpt-4-turbo")
            try:
                async for chunk in service.generate_stream(prompt=prompt, model=model):
                    await websocket.send_json({"delta": chunk, "finish_reason": None})
                await websocket.send_json({"delta": "", "finish_reason": "stop"})
            except ValueError as exc:
                await websocket.send_json({"error": str(exc)})
    except WebSocketDisconnect:
        logger.debug("WebSocket stream client disconnected")
