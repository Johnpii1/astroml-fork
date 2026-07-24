"""Natural Language Query API Router."""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.auth.dependencies import AuthContext, get_current_auth
from astroml.llm.query import (
    generate_sql,
    execute_safe_query,
    generate_pipeline_config,
    format_query_results,
    get_query_suggestions,
)
from astroml.llm.cost import check_budget, track_request

router = APIRouter(prefix="/api/v1/query", tags=["query"])


class NLQueryIn(BaseModel):
    query: str
    model: str = "gpt-3.5-turbo"
    mode: str = "sql"  # 'sql' or 'pipeline'
    feature: str = "nlp_query"


class NLQueryOut(BaseModel):
    query: str
    mode: str
    sql: Optional[str] = None
    pipeline_yaml: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    suggestions: List[str]


@router.post("", response_model=NLQueryOut)
async def post_natural_query(
    body: NLQueryIn,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    """
    Query database or generate pipeline using natural language.
    Includes validation, safety checks, audit logs and budgeting.
    """
    user_id = str(auth.user_id or auth.subject)
    
    # 1. Check budget first
    try:
        await check_budget(db, user_id, body.model)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Budget exceeded or model access denied: {str(e)}"
        )
        
    start_time = 0.0
    sql = None
    pipeline_yaml = None
    formatted_results = None
    
    # 2. Process query
    if body.mode == "sql":
        # Translate to SQL
        sql = generate_sql(body.query)
        try:
            # Execute safely
            raw_rows = await execute_safe_query(db, sql)
            formatted_results = format_query_results(raw_rows)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database query execution failed: {str(e)}"
            )
    elif body.mode == "pipeline":
        # Translate to ML Pipeline YAML configuration
        pipeline_yaml = generate_pipeline_config(body.query)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query mode '{body.mode}'. Supported: 'sql', 'pipeline'"
        )
        
    # 3. Track spending (mock usage metrics)
    input_tokens = len(body.query) // 4 + 1
    output_tokens = (len(sql or "") + len(pipeline_yaml or "")) // 4 + 1
    await track_request(
        db=db,
        user_id=user_id,
        feature=body.feature,
        model_name=body.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=150.0,  # mock latency
    )
    
    suggestions = get_query_suggestions()
    
    return NLQueryOut(
        query=body.query,
        mode=body.mode,
        sql=sql,
        pipeline_yaml=pipeline_yaml,
        results=formatted_results,
        suggestions=suggestions
    )
