from __future__ import annotations
import re
from typing import Optional

from app.models.request_model import FalloutRequest, ResponsePayload
from app.models.response_model import ClosedCase, FalloutMeta
from app.utils.pii_masker import mask, mask_if_sensitive, mask_payload
import json


def parse_description(
    description: Optional[str],
    response_payload: Optional[ResponsePayload] = None,
) -> dict:
    """
    Extract error_code, error_reason, error_message from the description field.
    Falls back to responsePayload.status when description does not contain error info.
    """
    code_val = reason_val = message_val = None

    if description:
        code    = re.search(r"Error Code\s*[-:]\s*(\S+)", description, re.IGNORECASE)
        reason  = re.search(r"Error Reason\s*[-:]\s*(.+?)(?=Error Message|$)", description, re.IGNORECASE | re.DOTALL)
        message = re.search(r"Error Message\s*[-:]\s*(.+?)$", description, re.IGNORECASE | re.DOTALL)

        code_val    = code.group(1).strip()    if code    else None
        reason_val  = reason.group(1).strip()  if reason  else None
        message_val = message.group(1).strip() if message else description.strip()

    # Fill gaps from responsePayload.status when description had no error info
    if response_payload and response_payload.status:
        status = response_payload.status
        if not code_val and status.code:
            code_val = status.code.strip()
        if not code_val and status.errorcode:
            code_val = status.errorcode.strip()
        if not reason_val and status.errorcode:
            reason_val = status.errorcode.strip()
        if not message_val and status.errormessage:
            message_val = status.errormessage.strip()

    return {
        "error_code":    code_val,
        "error_reason":  reason_val,
        "error_message": message_val,
    }


def build_fallout_prompt(
    request: FalloutRequest,
    top5_closed: list[ClosedCase],
    parsed: Optional[dict] = None,
) -> str:
    if parsed is None:
        parsed = parse_description(request.description, request.responsePayload)
    print("REQUEST", request)
    # Mask PII only in sensitive free-text fields
    error_reason  = mask_if_sensitive("description", parsed.get("error_reason") or "N/A")
    error_message = mask_if_sensitive("description", parsed.get("error_message") or "N/A")
    short_desc    = mask_if_sensitive("short_description", request.short_description or "N/A")
    resolution    = mask_if_sensitive("notes", request.u_resolution_notes or "None")
    work_notes    = mask_if_sensitive("work_notes", request.work_notes or "None")

    # Build closed cases section from top-5 history rows
    if top5_closed:
        cc_lines = ["## Similar Past Closed Cases"]
        for i, c in enumerate(top5_closed, 1):
            cc_lines.append(
                f"[CC-{i}] Ticket={c.ticket_number} | Source={c.resolution_source}"
                f"\n  Short Desc: {mask_if_sensitive('short_description', c.short_description) or 'N/A'}"
                f"\n  Resolution: {mask_if_sensitive('notes', c.resolution_notes) or 'N/A'}"
            )
        cc_section = "\n".join(cc_lines)
    else:
        cc_section = "## Similar Past Closed Cases\nNo similar closed cases found."

    masked_request_payload = (
        mask_payload(request.requestPayload.model_dump())
        if request.requestPayload else None
    )

    masked_response_payload = (
        mask_payload(request.responsePayload.model_dump())
        if request.responsePayload else None
    )
    request_payload_str = json.dumps(masked_request_payload, indent=2) if masked_request_payload else "N/A"
    response_payload_str = json.dumps(masked_response_payload, indent=2) if masked_response_payload else "N/A"
    prompt = (
        "You are a senior Order Management Analyst at Brightspeed telecom.\n"
        "Use the past closed cases below to suggest the best resolution.\n"
        "Respond ONLY with a valid JSON object. No markdown, no extra text.\n\n"

        "## Incident\n"
        f"Ticket: {request.number} | Order: {request.u_order_number or 'N/A'}\n"
        f"Short Desc: {short_desc} | Network: {request.u_network_type_boss or 'N/A'}\n"
        f"Action: {request.u_order_action or 'N/A'} | LOB: {request.u_lob or 'N/A'}\n"
        f"Group: {request.assignment_group or 'N/A'} / {request.u_sub_assignment_group or 'N/A'}\n"
        f"Category: {request.u_parent_categories or 'N/A'} > {request.u_sub_categories or 'N/A'}\n"
        f"Error Code: {parsed.get('error_code') or 'N/A'}\n"
        f"Error Reason: {error_reason}\n"
        f"Error Message: {error_message}\n"
        f"Resolution Notes: {resolution}\n"
        f"Work Notes: {work_notes}\n\n"

        "## Request Payload (Masked)\n"
        f"{request_payload_str}\n\n"

        "## Response Payload (Masked)\n"
        f"{response_payload_str}\n\n"

        f"{cc_section}\n\n"

        "Return like this JSON:\n"
        '{"root_cause":"string","resolution_steps":["step1","step2","step3"]}'
    )
    print ("PROMPT TO LLM: ", prompt)
    return prompt
    # (
    #     "You are a senior Order Management Analyst at Brightspeed telecom.\n"
    #     "Use the past closed cases below to suggest the best resolution.\n"
    #     "Respond ONLY with a valid JSON object. No markdown, no extra text.\n\n"
    #     "## Incident\n"
    #     f"Ticket: {request.number} | Order: {request.u_order_number or 'N/A'}\n"
    #     f"Short Desc: {short_desc} | Network: {request.u_network_type_boss or 'N/A'}\n"
    #     f"Action: {request.u_order_action or 'N/A'} | LOB: {request.u_lob or 'N/A'}\n"
    #     f"Group: {request.assignment_group or 'N/A'} / {request.u_sub_assignment_group or 'N/A'}\n"
    #     f"Category: {request.u_parent_categories or 'N/A'} > {request.u_sub_categories or 'N/A'}\n"
    #     f"Error Code: {parsed.get('error_code') or 'N/A'}\n"
    #     f"Error Reason: {error_reason}\n"
    #     f"Error Message: {error_message}\n"
    #     f"Resolution Notes: {resolution}\n"
    #     f"Work Notes: {work_notes}\n\n"
    #     f"{cc_section}\n\n"
    #     "Return this JSON:\n"
    #     '{"root_cause":"string","resolution_steps":["step1","step2","step3"],"escalation":"string","prevention":"string"}'
    # )
