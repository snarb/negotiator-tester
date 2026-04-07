## Backend Database Schema

### Integration Rule

External SQLite access must be **read-only**.

SQLite stores `DATETIME(timezone=true)` values as ISO-8601 text with timezone offset. In this runtime they are emitted in UTC-aware form.

Allowed use:

- dashboards;
- reporting;
- UI test observation;
- read-only reconciliation.

Forbidden use:

- inserting inbound or outbound records directly;
- updating ticket status or message history;
- modifying metadata JSON;
- schema migration, DDL, triggers, or indexes created by external tools.

### External-Facing Tables

The following tables are relevant for external UI/dashboard integrations.

#### `tickets`

Primary key:

- `ticket_id` `VARCHAR(255)`

Columns:

- `ticket_id` `VARCHAR(255)` not null, primary key
- `project_id` `VARCHAR(255)` nullable
- `status` `VARCHAR(32)` not null
- `closure_reason` `VARCHAR(64)` nullable
- `finalization_reason` `VARCHAR(64)` nullable
- `initial_stage_started` `BOOLEAN` not null
- `negotiation_stage_started` `BOOLEAN` not null
- `signal_history` `JSON` not null
- `payment_data_snapshot` `JSON` not null
- `messages` `JSON` not null
- `csat_score` `INTEGER` nullable
- `csat_received` `BOOLEAN` not null
- `dispute_detected` `BOOLEAN` not null
- `outcomes_last_synced_at` `DATETIME(timezone=true)` nullable
- `issued_refund_pct` `INTEGER` not null
- `granted_free_months` `INTEGER` not null
- `granted_bundle_id` `VARCHAR(32)` nullable
- `last_user_message_at` `DATETIME(timezone=true)` nullable
- `was_escalated_to_human` `BOOLEAN` not null
- `escalated_on_error` `BOOLEAN` not null
- `closed_at` `DATETIME(timezone=true)` nullable
- `finalized_at` `DATETIME(timezone=true)` nullable
- `created_at` `DATETIME(timezone=true)` not null
- `updated_at` `DATETIME(timezone=true)` not null
- `metadata` `JSON` not null

Notes for external consumers:

- `status`, `closure_reason`, and `finalization_reason` are the primary lifecycle fields for dashboards.
- `payment_data_snapshot` contains the latest stored payment context received from the public API.
- `messages` is the main audit trail for user messages, assistant messages, and tool-call traces.
- `csat_received` distinguishes "CSAT not received yet" from a populated `csat_score`.
- `outcomes_last_synced_at` shows when delayed CSAT/dispute outcomes were last checked successfully.
- `metadata.selected_arms` stores the chosen arms per lifecycle stage as a JSON object. The current keys are `persona`, `J1`, `J2`, `J4`, and `J5`. Values are the selected `arm_id` strings for that ticket.
- `metadata.available_bundle_id` stores the resolved bundle used to filter the negotiation ladder.
- `metadata.selected_ladder` stores the raw selected concession ladder before bundle-specific filtering.
- `metadata.filtered_ladder` stores the bundle-filtered concession ladder that is actually passed to negotiation-stage prompt construction and tool-plan validation.

Compact JSON shapes:

- `signal_history[*]`: JSON object with these exact keys:
  - `noticeable_anger`: `bool`
  - `confusion`: `bool`
  - `scam_framing`: `bool`
  - `app_was_used`: `"Unknown"` or a string with the detected app name
  - `high_price`: `bool`
  - `legal_or_threatening`: `bool`
- `messages[*]`: JSON object with one of these exact shapes:
  - `{"role": "user", "content": string}`
  - `{"role": "assistant", "content": string}`
  - `{"role": "assistant", "tool_calls": [...]}` where each tool call has `id`, `type`, and `function`
  - `{"role": "tool", "tool_call_id": string, "content": string}`
- `payment_data_snapshot` and inbound `payment_data`: free-form JSON objects; in practice they usually carry `owned_bundles` and other billing context.
- `metadata`: JSON object for ticket-specific structured observability. For `tickets`, it currently has these keys:
  - `selected_arms`: object with stage keys `persona`, `J1`, `J2`, `J4`, and `J5`, where each value is a selected `arm_id` string for that stage
  - `available_bundle_id`: string or `null`
  - `selected_ladder`: object describing the raw selected concession ladder before bundle-specific filtering
  - `filtered_ladder`: object describing the bundle-adjusted concession ladder actually used for negotiation prompt construction and tool-plan validation

#### `inbound_events`

Primary key:

- `event_id` `VARCHAR(36)`

Indexes:

- `ix_inbound_events_status`
- `ix_inbound_events_ticket_id`

Columns:

- `event_id` `VARCHAR(36)` not null, primary key
- `ticket_id` `VARCHAR(255)` not null
- `project_id` `VARCHAR(255)` nullable
- `message_text` `TEXT` not null
- `payment_data` `JSON` not null
- `metadata` `JSON` not null
- `status` `VARCHAR(32)` not null
- `error_message` `TEXT` nullable
- `claimed_at` `DATETIME(timezone=true)` nullable
- `processed_at` `DATETIME(timezone=true)` nullable
- `created_at` `DATETIME(timezone=true)` not null
- `updated_at` `DATETIME(timezone=true)` not null

Notes for external consumers:

- This table is the intake/audit record for public API submissions.
- `status` shows pipeline progress for an accepted inbound event.
- `error_message` is populated when event processing fails after acceptance.
- `metadata` is free-form request context from the caller.

#### `outbound_messages`

Primary key:

- `outbound_message_id` `VARCHAR(36)`

Indexes:

- `ix_outbound_messages_ticket_id`
- `ix_outbound_messages_send_at`
- `ix_outbound_messages_status`

Columns:

- `outbound_message_id` `VARCHAR(36)` not null, primary key
- `ticket_id` `VARCHAR(255)` not null
- `message_text` `TEXT` not null
- `send_at` `DATETIME(timezone=true)` not null
- `status` `VARCHAR(32)` not null
- `close_after_send` `BOOLEAN` not null
- `retry_count` `INTEGER` not null
- `created_at` `DATETIME(timezone=true)` not null
- `sent_at` `DATETIME(timezone=true)` nullable
- `metadata` `JSON` not null

Notes for external consumers:

- This table is the authoritative record for persisted outbound customer-visible responses.
- `status` shows whether a response is pending, sent, failed, or cancelled.
- `send_at` and `sent_at` support delivery timeline views.
- `metadata` may contain only minimal routing hints such as the linked `ticket_action_id`.

#### `ticket_actions`

Primary key:

- `ticket_action_id` `VARCHAR(36)`

Indexes:

- `ix_ticket_actions_ticket_id`
- `ix_ticket_actions_source`
- `ix_ticket_actions_action_name`
- `ix_ticket_actions_status`

Columns:

- `ticket_action_id` `VARCHAR(36)` not null, primary key
- `ticket_id` `VARCHAR(255)` not null
- `source` `VARCHAR(16)` not null
- `action_name` `VARCHAR(64)` not null
- `status` `VARCHAR(32)` not null
- `payload` `JSON` not null
- `external_action_id` `VARCHAR(255)` nullable
- `error_message` `TEXT` nullable
- `created_at` `DATETIME(timezone=true)` not null
- `completed_at` `DATETIME(timezone=true)` nullable

Notes for external consumers:

- This is the minimal authoritative action log for ticket-level side effects and queued sends.
- `source` is usually `tool` or `system`.
- Use it to see actions such as `REFUND`, `GRANT_BUNDLE`, `GRANT_3_FREE_MONTHS`, `ESCALATE_TO_HUMAN`, `CANCEL_SUBSCRIPTION`, and `SEND_RESPONSE`.
- `status` distinguishes requested, queued, succeeded, failed, and cancelled actions.
- `payload` stores only the minimal action arguments needed for replay and dashboarding.

### Internal Tables Excluded From External Use

The database also contains internal tables that are not part of the external integration contract and must not be relied on by dashboards or UI testing tools. `persistent_samples` remains intentionally omitted from this ICD because it is primarily internal learning data rather than a stable external contract.

### `tickets.messages` JSON Structure

The `tickets.messages` JSON array may contain multiple message object shapes relevant to external observation.

Customer message:

```json
{
  "role": "user",
  "content": "I want a refund"
}
```

Assistant message:

```json
{
  "role": "assistant",
  "content": "We have issued a refund."
}
```

Assistant tool-call trace:

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "string",
      "type": "function",
      "function": {
        "name": "REFUND",
        "arguments": "{\"refund_pct\":30}"
      }
    }
  ]
}
```

Tool result trace:

```json
{
  "role": "tool",
  "tool_call_id": "string",
  "content": "{\"status\":\"ok\"}"
}
```

For UI testing and audit visualization:

- use `outbound_messages` to show persisted customer-visible replies;
- use `tickets.messages` to show conversational history and tool-call traces;
- use `ticket_actions` as the authoritative execution log for queued and executed actions;
- do not assume that every assistant tool-call trace implies a completed external side effect.

## Constants/Enums

### Ticket Status

Allowed values:

- `OPEN`
- `CLOSED`
- `FINALIZED`

### Closure Reason

Allowed values:

- `closed_by_negotiation_tool`
- `closed_by_inactivity_job`

### Finalization Reason

Allowed values:

- `dispute`
- `max_reopen_interval_expired`
- `escalated_to_human`

### Inbound Event Status

Allowed values:

- `PENDING`
- `CLAIMED`
- `PROCESSED`
- `FAILED`

### Outbound Message Status

Allowed values:

- `PENDING`
- `SENT`
- `FAILED`
- `CANCELLED`

### Message Role

Allowed values in `tickets.messages[*].role`:

- `user`
- `assistant`
- `tool`

### Tool Invocation Names Persisted in Trace

Allowed tool names currently persisted in `tickets.messages[*].tool_calls[*].function.name`:

- `HANDOFF_TO_NEGOTIATION_STAGE`
- `ESCALATE_TO_HUMAN`
- `REFUND`
- `GRANT_BUNDLE`
- `GRANT_3_FREE_MONTHS`
- `SEND_RESPONSE`

### Delay Values

Allowed values for persisted `SEND_RESPONSE.delay` arguments:

- `no`
- `short`
- `mid`
- `long`

### Ticket Action Status

Allowed values:

- `REQUESTED`
- `QUEUED`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
