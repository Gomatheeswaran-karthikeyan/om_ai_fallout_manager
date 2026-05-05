-- AI Fallout Manager – full schema reset
-- Run this once against your PostgreSQL database.

-- ── 1. Meta / Knowledge Base table ───────────────────────────────────────────

DROP TABLE IF EXISTS bosssvc.AI_FALLOUTS_META_DESCRIPTION CASCADE;

CREATE TABLE bosssvc.AI_FALLOUTS_META_DESCRIPTION (
    id                  SERIAL PRIMARY KEY,
    number              VARCHAR(100),           -- reference case / ticket number
    task_description    TEXT,                   -- what the task/order was doing
    description         TEXT,                   -- error description pattern
    short_description   VARCHAR(500),           -- short description keyword pattern
    error_code          VARCHAR(100),           -- exact error code for direct lookup (e.g. TIMEOUT, 400)
    network_type        VARCHAR(50),            -- Copper | Fiber | Coax | All
    order_action        VARCHAR(100),           -- e.g. NEW_INSTALL, CHANGE, DISCONNECT
    lob                 VARCHAR(100),           -- Line of Business
    case_status         VARCHAR(50),            -- e.g. Closed, Resolved
    work_notes          TEXT,                   -- internal work notes
    resolution_notes    TEXT NOT NULL,          -- known resolution (required)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2. Closed Cases History table ────────────────────────────────────────────

DROP TABLE IF EXISTS bosssvc.AI_FALLOUTS_CLOSED_CASES CASCADE;

CREATE TABLE bosssvc.AI_FALLOUTS_CLOSED_CASES (
    id                  SERIAL PRIMARY KEY,
    ticket_number       VARCHAR(100) NOT NULL,
    order_number        VARCHAR(200),
    short_description   VARCHAR(500),
    description         TEXT,
    network_type        VARCHAR(50),
    order_action        VARCHAR(100),
    lob                 VARCHAR(100),
    fallout_type        VARCHAR(150),
    error_code          VARCHAR(50),
    resolution_source   VARCHAR(30) NOT NULL
                            CHECK (resolution_source IN
                                ('AI_SUGGESTION','RESOLUTION_NOTES','WORK_NOTES','MANUAL')),
    resolution_notes    TEXT,
    work_notes          TEXT,
    ai_suggestion       JSONB,                  -- stored only when source = AI_SUGGESTION
    closed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_closed_cases_ticket  ON bosssvc.AI_FALLOUTS_CLOSED_CASES (ticket_number);
CREATE INDEX idx_closed_cases_error   ON bosssvc.AI_FALLOUTS_CLOSED_CASES (error_code);
CREATE INDEX idx_closed_cases_network ON bosssvc.AI_FALLOUTS_CLOSED_CASES (network_type);

-- ── 3. Auto-update trigger ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION bosssvc.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_meta_updated_at ON bosssvc.AI_FALLOUTS_META_DESCRIPTION;
CREATE TRIGGER trg_meta_updated_at
    BEFORE UPDATE ON bosssvc.AI_FALLOUTS_META_DESCRIPTION
    FOR EACH ROW EXECUTE FUNCTION bosssvc.update_updated_at_column();

-- ── 4. Seed data ─────────────────────────────────────────────────────────────

-- 4a. Curated knowledge base (exact match by error_code + network_type + order_action)
INSERT INTO bosssvc.AI_FALLOUTS_META_DESCRIPTION
    (number, description, short_description, error_code,
     network_type, order_action, lob, case_status, work_notes, resolution_notes)
VALUES
(
    'CS11414205',
    'Tech called in for no service light. ONT not linked in EMS or cloud after order activation.',
    'ONT Manually Activated EMS CMS SMX',
    NULL,
    'Brspd', 'Add', NULL, 'Closed', NULL,
    'Manually link ONT in EMS and cloud portal. Link RG in cloud. Push latest firmware update. Confirm all service lights green before closing. If ONT remains offline after 2 attempts, escalate to NOC Level 2.'
),
(
    'CS11657556',
    'BRIM API returned error: No Contract found to cancel for the given BAN and Product.',
    'Update Subscription in BRIM',
    'TIMEOUT',
    'Brspd', 'Change', NULL, 'Closed',
    'BRIM KAFKA RESPONSE NOT RECEIVED WITHIN 60 MIN — system timed out waiting for BRIM acknowledgement.',
    'BRIM KAFKA timeout: Verify BRIM contract exists for the given BAN and Product. If contract is present, retry the cancellation after confirming KAFKA topic is healthy. If contract is missing, escalate to BRIM support team. Check SuccessCount/FailedCount in BRIM audit logs before retrying.'
);

-- 4b. Historical closed cases go into AI_FALLOUTS_CLOSED_CASES (used as LLM context).
-- AI_FALLOUTS_META_DESCRIPTION is the curated knowledge base — add entries manually.

INSERT INTO bosssvc.AI_FALLOUTS_CLOSED_CASES
    (ticket_number, short_description, description,
     network_type, order_action, lob, resolution_source, work_notes, resolution_notes)
VALUES
(
    'CS11657556',
    'Update Subscription in BRIM',
    'Error Code - 400 Error Reason - No Contract found to cancel for the input BAN: 310044491, Product: 4235434909 Error Message -',
    'Brspd', 'Change', NULL, 'RESOLUTION_NOTES',
    'System work note: BRIM API returned 400 - No Contract found to cancel for BAN: 310044491, Product: 4235434909. SuccessCount:0 FailedCount:1.',
    'Error Code - 400 Error Reason - No Contract found to cancel for the input BAN: 310044491, Product: 4235434909. Verify contract exists in BRIM for the given BAN and product before attempting cancellation. If contract is missing, escalate to BRIM support team.'
),
(
    'CS10845809',
    'Company Action',
    'Please reach out to the cx to get her rescheduled. Thank you!',
    'Brspd', 'Add', NULL, 'MANUAL', NULL,
    'Review Company Action. Refer to previous case CS09128309. No action taken. Close case. Escalate to COR if further action required.'
),
(
    'CS09146572',
    'Customer Reqs Reschedule SubReason requests reschedule Category Customer Miss',
    'TX1100028757 - ReasonCode: Customer Reqs Reschedule',
    'Brspd', 'Add', NULL, 'RESOLUTION_NOTES',
    '1st attempt for reschedule routed to vm, left message and sent email. Follow-up set for 10/09/2025.',
    'Contacted customer for 2nd reschedule attempt. No answer, left voicemail, sent follow-up email. Closing case after exhausting contact attempts.'
),
(
    'CS11414205',
    'ONT Manually Activated EMS CMS SMX',
    'Tech called in for no service light. Manually linked ONT in EMS and the cloud, also linked RG in the cloud. Pushed most current update, everything green and working successfully.',
    'Brspd', 'Add', NULL, 'RESOLUTION_NOTES', NULL,
    'Manually linked ONT in EMS and cloud. Linked RG in cloud. Pushed latest firmware update. All lights green and service restored successfully.'
),
(
    'CS09740535',
    'Pending Order description required facilities',
    'Chat rep could not see facilities. LR came up for me.',
    'Brspd', NULL, NULL, 'MANUAL', NULL,
    'Provided facility information to chat rep. LR lookup successful. Facility details shared to complete the pending order.'
),
(
    'CS09205275',
    'Contacted COR Order assistance voip port rejected',
    'Tech called in for voip not able to make calls. Port showing rejected, contacted COR and created a ticket to have port pushed back through.',
    'Brspd', 'Add', NULL, 'RESOLUTION_NOTES', NULL,
    'Tech called for VOIP issue - port showing rejected. Contacted COR team and raised ticket to push port back through. Port restored and VOIP calls confirmed working.'
),
(
    'CS09168153',
    'Advise customer order cancelled 4G services not available',
    'Outbound call required - 4G services not available for customer address, order must be cancelled.',
    NULL, 'Add', NULL, 'MANUAL', NULL,
    'Attempted outbound call to customer regarding 4G service cancellation. No answer. Left detailed voicemail per script with callback number 833-692-7772. Sent follow-up email. Case closed after contact attempt.'
),
(
    'CS09143843',
    'ONT Swap BOSS Change',
    'ONT swap requested via BOSS system',
    'Brspd', 'Change', NULL, 'RESOLUTION_NOTES', NULL,
    'ONT swap completed via BOSS. New ONT provisioned and activated successfully. Service restored.'
),
(
    'CS09140785',
    'Provided Facility Information SIP tech',
    'Tech requested SIP information for facility. Provided SIP details.',
    'Copper', NULL, NULL, 'RESOLUTION_NOTES', NULL,
    'Provided SIP facility information to tech. Tech confirmed details and completed installation successfully.'
);
