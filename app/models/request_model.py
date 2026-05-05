from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class ResponseStatus(BaseModel):
    """Error status from the system response payload."""
    errormessage: Optional[str] = None
    code: Optional[str] = None
    errorcode: Optional[str] = None


class InnerResponse(BaseModel):
    success: Optional[str] = None
    accountNumber: Optional[str] = Field(None, description="PII - not sent to LLM")
    bossOrderId: Optional[str] = None
    jobId: Optional[str] = None


class ResponsePayload(BaseModel):
    """Structured response from the downstream system (e.g. BRIM, BOSS)."""
    jobId: Optional[str] = None
    response: Optional[InnerResponse] = None
    status: Optional[ResponseStatus] = None


class FalloutRequest(BaseModel):
    """Matches the ServiceNow fallout incident payload exactly."""

    number: str = Field(..., description="Ticket / incident number e.g. CS11749584")
    account: Optional[str] = Field(None, description="Customer account (PII - not sent to LLM)")
    opened_at: Optional[str] = None
    sys_created_by: Optional[str] = None
    sys_updated_on: Optional[str] = None
    sys_updated_by: Optional[str] = Field(None, description="PII - not sent to LLM")
    state: Optional[str] = None
    state_value: Optional[str] = None
    due_date: Optional[str] = None
    assignment_group: Optional[str] = None
    u_sub_assignment_group: Optional[str] = None
    u_parent_categories: Optional[str] = None
    u_sub_categories: Optional[str] = None
    assigned_to: Optional[str] = Field(None, description="PII - not sent to LLM")
    short_description: Optional[str] = None
    u_network_type_boss: Optional[str] = None
    u_order_number: Optional[str] = None
    u_order_action: Optional[str] = None
    u_lob: Optional[str] = None
    description: Optional[str] = None
    resolved_by: Optional[str] = Field(None, description="PII - not sent to LLM")
    closed_by: Optional[str] = Field(None, description="PII - not sent to LLM")
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    u_resolution_notes: Optional[str] = None
    work_notes: Optional[str] = None
    responsePayload: Optional[ResponsePayload] = Field(
        None, description="Structured downstream system response with error status"
    )


class CloseCaseRequest(BaseModel):
    """Payload to record a resolved fallout case into history."""

    ticket_number: str
    order_number: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    network_type: Optional[str] = None
    order_action: Optional[str] = None
    lob: Optional[str] = None
    fallout_type: Optional[str] = None
    error_code: Optional[str] = None
    resolution_source: Literal["AI_SUGGESTION", "RESOLUTION_NOTES", "WORK_NOTES", "MANUAL"]
    resolution_notes: Optional[str] = None
    work_notes: Optional[str] = None
    ai_suggestion: Optional[dict[str, Any]] = Field(
        None, description="The AI suggestion object, required when source is AI_SUGGESTION"
    )
