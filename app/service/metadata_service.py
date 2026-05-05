from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.queries import fetch_all_meta, fetch_exact_meta
from app.models.response_model import FalloutMeta


async def get_exact_meta(
    session: AsyncSession,
    error_code: Optional[str] = None,
    network_type: Optional[str] = None,
    order_action: Optional[str] = None,
    lob: Optional[str] = None,
) -> Optional[FalloutMeta]:
    return await fetch_exact_meta(session, error_code, network_type, order_action, lob)


async def list_all_meta(session: AsyncSession) -> list[FalloutMeta]:
    return await fetch_all_meta(session)
