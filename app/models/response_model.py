from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel


class FalloutMeta(BaseModel):
    id: int
    number: Optional[str]
    task_description: Optional[str]
    description: Optional[str]
    short_description: Optional[str]
    error_code: Optional[str]
    network_type: Optional[str]
    order_action: Optional[str]
    lob: Optional[str]
    case_status: Optional[str]
    work_notes: Optional[str]
    resolution_notes: str
    created_at: datetime
    updated_at: datetime


class ClosedCase(BaseModel):
    id: int
    ticket_number: str
    order_number: Optional[str]
    short_description: Optional[str]
    description: Optional[str]
    network_type: Optional[str]
    order_action: Optional[str]
    lob: Optional[str]
    fallout_type: Optional[str]
    error_code: Optional[str]
    resolution_source: str
    resolution_notes: Optional[str]
    work_notes: Optional[str]
    ai_suggestion: Optional[dict[str, Any]]
    closed_at: datetime
    created_at: datetime


class AISuggestion(BaseModel):
    # root_cause: str
    resolution_steps: list[str]
    # escalation: str
    # prevention: str


class FalloutAnalysisResponse(BaseModel):
    ticket_number: str
    order_number: Optional[str]
    fallout_type: Optional[str]
    error_code: Optional[str]
    resolution_source: Literal["META_DIRECT", "LLM_SUGGESTION"]
    meta_found: bool
    suggestion: str | AISuggestion


class CloseCaseResponse(BaseModel):
    success: bool
    ticket_number: str
    message: str
