from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_model import FalloutRequest
from app.models.response_model import FalloutAnalysisResponse
from app.service.metadata_service import get_exact_meta
from app.service.llm_service import get_ai_suggestion
from app.db.queries import fetch_top5_closed
from app.utils.prompt_builder import build_fallout_prompt, parse_description


async def analyze_fallout(
    session: AsyncSession,
    request: FalloutRequest,
) -> FalloutAnalysisResponse:
    parsed       = parse_description(request.description, request.responsePayload)
    error_code   = parsed["error_code"] or "UNKNOWN"
    fallout_type = request.u_sub_categories or request.u_parent_categories

    # ── Step 1: exact meta lookup by error_code ───────────────────────────────
    try:
        meta = await get_exact_meta(
            session,
            error_code=error_code,
            network_type=request.u_network_type_boss,
            order_action=request.u_order_action,
            lob=request.u_lob,
        )
    except Exception as exc:
        raise RuntimeError(f"DB error (meta): {exc}") from exc

    # ── Step 2: exact match found — return resolution directly, no LLM ───────
    if meta:
        return FalloutAnalysisResponse(
            ticket_number=request.number,
            order_number=request.u_order_number,
            fallout_type=fallout_type,
            error_code=error_code,
            resolution_source="META_DIRECT",
            meta_found=True,
            suggestion=meta.resolution_notes,
        )

    # ── Step 3: no meta match — fetch similar closed cases for LLM context ───
    try:
        top5_closed = await fetch_top5_closed(
            session,
            short_description=request.short_description,
            description=request.description,
            network_type=request.u_network_type_boss,
            error_code=error_code,
        )
    except Exception as exc:
        raise RuntimeError(f"DB error (closed cases): {exc}") from exc

    # ── Step 4: ask LLM with closed cases as context ─────────────────────────
    try:
        prompt        = build_fallout_prompt(request, top5_closed, parsed)
        ai_suggestion = await get_ai_suggestion(prompt)
    except Exception as exc:
        raise RuntimeError(f"LLM error ({type(exc).__name__}): {exc}") from exc

    return FalloutAnalysisResponse(
        ticket_number=request.number,
        order_number=request.u_order_number,
        fallout_type=fallout_type,
        error_code=error_code,
        resolution_source="LLM_SUGGESTION",
        meta_found=False,
        suggestion=ai_suggestion,
    )
