from __future__ import annotations

import json
import re
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.response_model import ClosedCase, FalloutMeta

_STOP_WORDS = {"the", "and", "for", "are", "was", "not", "with", "this", "that", "from"}

_META_TABLE   = f"{settings.db_schema}.AI_FALLOUTS_META_DESCRIPTION"
_CLOSED_TABLE = f"{settings.db_schema}.AI_FALLOUTS_CLOSED_CASES"

_META_COLS = (
    "id, number, task_description, description, short_description, error_code, "
    "network_type, order_action, lob, case_status, work_notes, "
    "resolution_notes, created_at, updated_at"
)

_CLOSED_COLS = (
    "id, ticket_number, order_number, short_description, description, "
    "network_type, order_action, lob, fallout_type, error_code, "
    "resolution_source, resolution_notes, work_notes, ai_suggestion, "
    "closed_at, created_at"
)


def _keywords(value: Optional[str]) -> list[str]:
    if not value:
        return []
    words = re.findall(r"[a-zA-Z0-9]+", value)
    return [w for w in words if len(w) > 3 and w.lower() not in _STOP_WORDS]


def _kw_score_expr(keywords: list[str], column: str, params: dict, prefix: str) -> str:
    if not keywords:
        return "0"
    clauses = []
    for i, kw in enumerate(keywords):
        p = f"{prefix}_{i}"
        clauses.append(f"CASE WHEN LOWER({column}) LIKE LOWER(:{p}) THEN 1 ELSE 0 END")
        params[p] = f"%{kw}%"
    return " + ".join(clauses)


# ── Meta queries ───────────────────────────────────────────────────────────────

async def fetch_exact_meta(
    session: AsyncSession,
    error_code: Optional[str] = None,
    network_type: Optional[str] = None,
    order_action: Optional[str] = None,
    lob: Optional[str] = None,
) -> Optional[FalloutMeta]:
    """
    Exact meta lookup:
      1. Must match error_code (if provided and non-UNKNOWN).
      2. Among matches, rank by how many of network_type / order_action / lob also match.
      3. Returns the single best row, or None if no error_code match exists.
    """
    if not error_code or error_code.upper() == "UNKNOWN":
        return None

    params: dict = {
        "error_code": error_code.upper(),
        "network_type": network_type,
        "order_action": order_action,
        "lob": lob,
    }

    sql = text(
        f"SELECT {_META_COLS},"
        " (CASE WHEN UPPER(error_code) = UPPER(:error_code) THEN 10 ELSE 0 END"
        " + CASE WHEN network_type IS NOT DISTINCT FROM :network_type THEN 3 ELSE 0 END"
        " + CASE WHEN order_action IS NOT DISTINCT FROM :order_action THEN 2 ELSE 0 END"
        " + CASE WHEN lob IS NOT DISTINCT FROM :lob THEN 1 ELSE 0 END"
        " ) AS match_score"
        f" FROM {_META_TABLE}"
        " WHERE UPPER(error_code) = UPPER(:error_code)"
        " ORDER BY match_score DESC"
        " LIMIT 1"
    )

    result = await session.execute(sql, params)
    row = result.mappings().first()
    if row is None:
        return None
    data = {k: v for k, v in row.items() if k != "match_score"}
    return FalloutMeta(**data)


# ── Closed cases queries ───────────────────────────────────────────────────────

async def fetch_top5_closed(
    session: AsyncSession,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    network_type: Optional[str] = None,
    error_code: Optional[str] = None,
) -> list[ClosedCase]:
    """Return up to 5 similar past closed cases for LLM context."""
    params: dict = {
        "network_type": network_type or "All",
        "error_code": error_code,
    }

    sd_kw   = _keywords(short_description)[:5]
    desc_kw = _keywords(description)[:4]

    sd_score   = _kw_score_expr(sd_kw,   "short_description", params, "csd")
    desc_score = _kw_score_expr(desc_kw, "description",       params, "cds")

    sql = text(
        f"SELECT {_CLOSED_COLS},"
        " (CASE WHEN error_code IS NOT DISTINCT FROM :error_code THEN 3 ELSE 0 END"
        " + CASE WHEN network_type = :network_type THEN 1 ELSE 0 END"
        f" + ({sd_score})"
        f" + ({desc_score})"
        " ) AS match_score"
        f" FROM {_CLOSED_TABLE}"
        " ORDER BY match_score DESC, closed_at DESC"
        " LIMIT 5"
    )

    result = await session.execute(sql, params)
    rows = result.mappings().all()
    out = []
    for row in rows:
        if row["match_score"] == 0:
            continue
        data = {k: v for k, v in row.items() if k != "match_score"}
        # asyncpg returns JSONB as a string or dict; normalise to dict
        if isinstance(data.get("ai_suggestion"), str):
            try:
                data["ai_suggestion"] = json.loads(data["ai_suggestion"])
            except Exception:
                data["ai_suggestion"] = None
        out.append(ClosedCase(**data))
    return out


async def insert_closed_case(session: AsyncSession, payload: dict) -> None:
    ai_val = payload.get("ai_suggestion")
    if isinstance(ai_val, dict):
        ai_val = json.dumps(ai_val)

    sql = text(
        f"INSERT INTO {_CLOSED_TABLE}"
        " (ticket_number, order_number, short_description, description,"
        "  network_type, order_action, lob, fallout_type, error_code,"
        "  resolution_source, resolution_notes, work_notes, ai_suggestion)"
        " VALUES"
        " (:ticket_number, :order_number, :short_description, :description,"
        "  :network_type, :order_action, :lob, :fallout_type, :error_code,"
        "  :resolution_source, :resolution_notes, :work_notes, :ai_suggestion)"
    )
    await session.execute(sql, {**payload, "ai_suggestion": ai_val})
    await session.commit()


# ── Meta list (for /meta endpoint) ────────────────────────────────────────────

async def fetch_all_meta(session: AsyncSession) -> list[FalloutMeta]:
    sql = text(f"SELECT {_META_COLS} FROM {_META_TABLE} ORDER BY id")
    result = await session.execute(sql)
    return [FalloutMeta(**row) for row in result.mappings().all()]
