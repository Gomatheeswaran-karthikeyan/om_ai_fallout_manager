from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.queries import insert_closed_case
from app.models.request_model import CloseCaseRequest
from app.models.response_model import CloseCaseResponse


async def record_closed_case(
    session: AsyncSession,
    req: CloseCaseRequest,
) -> CloseCaseResponse:
    payload = {
        "ticket_number":     req.ticket_number,
        "order_number":      req.order_number,
        "short_description": req.short_description,
        "description":       req.description,
        "network_type":      req.network_type,
        "order_action":      req.order_action,
        "lob":               req.lob,
        "fallout_type":      req.fallout_type,
        "error_code":        req.error_code,
        "resolution_source": req.resolution_source,
        "resolution_notes":  req.resolution_notes,
        "work_notes":        req.work_notes,
        "ai_suggestion":     req.ai_suggestion,
    }

    try:
        await insert_closed_case(session, payload)
        return CloseCaseResponse(
            success=True,
            ticket_number=req.ticket_number,
            message=f"Case {req.ticket_number} recorded as closed via {req.resolution_source}.",
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to record closed case: {exc}") from exc
