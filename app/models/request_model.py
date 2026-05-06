# from __future__ import annotations
# from typing import Any, Literal, Optional
# from pydantic import BaseModel, Field


# class ResponseStatus(BaseModel):
#     """Error status from the system response payload."""
#     errormessage: Optional[str] = None
#     code: Optional[str] = None
#     errorcode: Optional[str] = None


# class InnerResponse(BaseModel):
#     success: Optional[str] = None
#     accountNumber: Optional[str] = Field(None, description="PII - not sent to LLM")
#     bossOrderId: Optional[str] = None
#     jobId: Optional[str] = None


# class ResponsePayload(BaseModel):
#     """Structured response from the downstream system (e.g. BRIM, BOSS)."""
#     jobId: Optional[str] = None
#     response: Optional[InnerResponse] = None
#     status: Optional[ResponseStatus] = None

# class RequestPayload(BaseModel):
#     serviceType: Optional[str]
#     disconnectDate: Optional[str]
#     accountNum: Optional[int]
#     numberEngineers: Optional[int]
#     autoGenBSW: Optional[str]
#     hostTrackingNum: Optional[str]

#     customerInfo: Optional[CustomerInfo]
#     appointment: Optional[Appointment]

#     ows: Optional[bool]
#     dropLength: Optional[str]
#     preSurveyInd: Optional[str]

#     altCorrelationId: Optional[float]   # large number → float/scientific
#     altTrackingNum: Optional[int]

#     crdDate: Optional[str]
#     features: Optional[List]

#     wireCenter: Optional[str]
#     taskType: Optional[str]
#     customerType: Optional[str]
#     dispatchReady: Optional[bool]
#     isInside: Optional[bool]
#     lnpInd: Optional[str]

#     productType: Optional[str]
#     order: Optional[Order]

#     tncktId: Optional[int]
#     dropPlaced: Optional[str]
#     inquiryInterval: Optional[int]
#     priority: Optional[int]
#     voiceCategory: Optional[str]

#     transactionId: Optional[int]
#     dropType: Optional[str]
#     actionType: Optional[str]

#     jobLocation: Optional[JobLocation]

#     originatingSystem: Optional[str]
#     installType: Optional[str]
#     isHybrid: Optional[str]
#     callingSystem: Optional[str]

#     placement: Optional[str]
#     openDate: Optional[str]

# class FalloutRequest(BaseModel):
#     """Matches the ServiceNow fallout incident payload exactly."""

#     number: str = Field(..., description="Ticket / incident number e.g. CS11749584")
#     account: Optional[str] = Field(None, description="Customer account (PII - not sent to LLM)")
#     opened_at: Optional[str] = None
#     sys_created_by: Optional[str] = None
#     sys_updated_on: Optional[str] = None
#     sys_updated_by: Optional[str] = Field(None, description="PII - not sent to LLM")
#     state: Optional[str] = None
#     state_value: Optional[str] = None
#     due_date: Optional[str] = None
#     assignment_group: Optional[str] = None
#     u_sub_assignment_group: Optional[str] = None
#     u_parent_categories: Optional[str] = None
#     u_sub_categories: Optional[str] = None
#     assigned_to: Optional[str] = Field(None, description="PII - not sent to LLM")
#     short_description: Optional[str] = None
#     u_network_type_boss: Optional[str] = None
#     u_order_number: Optional[str] = None
#     u_order_action: Optional[str] = None
#     u_lob: Optional[str] = None
#     description: Optional[str] = None
#     resolved_by: Optional[str] = Field(None, description="PII - not sent to LLM")
#     closed_by: Optional[str] = Field(None, description="PII - not sent to LLM")
#     resolved_at: Optional[str] = None
#     closed_at: Optional[str] = None
#     u_resolution_notes: Optional[str] = None
#     work_notes: Optional[str] = None
#     responsePayload: Optional[ResponsePayload] = Field(
#         None, description="Structured downstream system response with error status"
#     )
#     requestPayload: Optional[RequestPayload] = Field(
#         None, description="Original request payload sent to downstream system"
#     )


# class CloseCaseRequest(BaseModel):
#     """Payload to record a resolved fallout case into history."""

#     ticket_number: str
#     order_number: Optional[str] = None
#     short_description: Optional[str] = None
#     description: Optional[str] = None
#     network_type: Optional[str] = None
#     order_action: Optional[str] = None
#     lob: Optional[str] = None
#     fallout_type: Optional[str] = None
#     error_code: Optional[str] = None
#     resolution_source: Literal["AI_SUGGESTION", "RESOLUTION_NOTES", "WORK_NOTES", "MANUAL"]
#     resolution_notes: Optional[str] = None
#     work_notes: Optional[str] = None
#     ai_suggestion: Optional[dict[str, Any]] = Field(
#         None, description="The AI suggestion object, required when source is AI_SUGGESTION"
#     )


from __future__ import annotations
from typing import Any, Literal, Optional, List, Dict
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Request Payload Models (Nested)
# ─────────────────────────────────────────────────────────────

class GeoLocation(BaseModel):
    latLonAccuracy: Optional[str]
    resolutionLevel: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class JobLocation(BaseModel):
    zipCode: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address2: Optional[str]
    geoLocation: Optional[GeoLocation]
    street: Optional[str]
    addressSubType: Optional[str]
    state: Optional[str]
    addressId: Optional[str]


class Remark(BaseModel):
    remarkText: Optional[str]
    remarkType: Optional[str]


class Order(BaseModel):
    remarks: Optional[List[Remark]]


class Appointment(BaseModel):
    dueDate: Optional[str]
    apptStart: Optional[str]
    apptFinish: Optional[str]
    earlyStart: Optional[str]


class CustomerInfo(BaseModel):
    phoneNumber: Optional[str]
    timezone: Optional[str]
    customerEmail: Optional[str]
    tranSMSPrimaryConsentFlag: Optional[str]
    customerName: Optional[str]


# ─────────────────────────────────────────────────────────────
# Request Payload Main Model
# ─────────────────────────────────────────────────────────────

class RequestPayload(BaseModel):
    serviceType: Optional[str]
    disconnectDate: Optional[str]
    accountNum: Optional[int]
    numberEngineers: Optional[int]
    autoGenBSW: Optional[str]
    hostTrackingNum: Optional[str]

    customerInfo: Optional[CustomerInfo]
    appointment: Optional[Appointment]

    ows: Optional[bool]
    dropLength: Optional[str]
    preSurveyInd: Optional[str]

    altCorrelationId: Optional[float]   # scientific notation safe
    altTrackingNum: Optional[int]

    crdDate: Optional[str]
    features: Optional[List[Any]]

    wireCenter: Optional[str]
    taskType: Optional[str]
    customerType: Optional[str]
    dispatchReady: Optional[bool]
    isInside: Optional[bool]
    lnpInd: Optional[str]

    productType: Optional[str]
    order: Optional[Order]

    tncktId: Optional[int]
    dropPlaced: Optional[str]
    inquiryInterval: Optional[int]
    priority: Optional[int]
    voiceCategory: Optional[str]

    transactionId: Optional[int]
    dropType: Optional[str]
    actionType: Optional[str]

    jobLocation: Optional[JobLocation]

    originatingSystem: Optional[str]
    installType: Optional[str]
    isHybrid: Optional[str]
    callingSystem: Optional[str]

    placement: Optional[str]
    openDate: Optional[str]


# ─────────────────────────────────────────────────────────────
# Main Fallout Request
# ─────────────────────────────────────────────────────────────

class FalloutRequest(BaseModel):
    """Matches the ServiceNow fallout incident payload exactly."""

    number: str = Field(..., description="Ticket / incident number e.g. CS11749584")

    account: Optional[str] = Field(None, description="PII - not sent to LLM")
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

    # responsePayload: Optional[ResponsePayload] = Field(
    #     None, description="Structured downstream system response with error status"
    # )

    # requestPayload: Optional[RequestPayload] = Field(
    #     None, description="Original request payload sent to downstream system"
    # )
    responsePayload: Optional[Dict[str, Any]] = Field(
        None, description="Dynamic downstream response payload"
    )

    requestPayload: Optional[Dict[str, Any]] = Field(
        None, description="Dynamic request payload sent to downstream system"
    )


# ─────────────────────────────────────────────────────────────
# Close Case Request
# ─────────────────────────────────────────────────────────────

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

    resolution_source: Literal[
        "AI_SUGGESTION",
        "RESOLUTION_NOTES",
        "WORK_NOTES",
        "MANUAL"
    ]

    resolution_notes: Optional[str] = None
    work_notes: Optional[str] = None

    ai_suggestion: Optional[Dict[str, Any]] = Field(
        None,
        description="The AI suggestion object, required when source is AI_SUGGESTION"
    )