## APIs

The system uses two authenticated HTTP APIs.
**Note on `project_id`**: In v1, the `project_id` parameter is **ignored** by the backend logic.

### Inbound Server API

This is **our API**.  
The external platform calls it when a new ticket or a new inbound user message arrives.

Purpose:

- validate the request;
- store the inbound event;
- enqueue asynchronous processing;
- return an immediate status.

Authentication:

```http
Authorization: Bearer <token>
````

The request is accepted only if:

- `ticket_id` is present as string;
- `message_text` is present and not empty;
- `payment_data` is not empty.

`project_id` field is optional in v1 and could be empty

If validation succeeds, the API returns success immediately and the message is processed asynchronously.  
`status = ok` means **accepted for asynchronous processing**, not fully processed.

Suggested endpoint:

```http
POST /api/v1/inbound/messages
```

Request:

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "message_text": "string",
  "payment_data": {},
  "metadata": {}
}
```

Success response:

```json
{
  "status": "ok"
}
```

Error response:

```json
{
  "status": "error",
  "error_code": "validation_error",
  "message": "payment_data is required and message_text must be non-empty"
}
```

**Lifecycle rejection rule:**

If the inbound request references a ticket that is already `FINALIZED` and `Ticket.was_escalated_to_human = true`, the API must reject the message and return an error response instead of accepting it for asynchronous processing. In this case, the backend must not call `_escalate_to_human()` again.

Example:

```json
{
  "status": "error",
  "error_code": "ticket_finalized_and_already_escalated",
  "message": "This ticket is finalized and already routed to human support."
}
```

### Outbound Action API

This is the **external API** that our system calls when it needs to send a message or execute an external action.



Authentication:

```http
Authorization: Bearer <token>
```

Suggested endpoints:

```http
POST /external-api/v1/messages/send
POST /external-api/v1/actions/refund
POST /external-api/v1/actions/cancel-subscription
POST /external-api/v1/actions/grant-free-months
POST /external-api/v1/actions/grant-bundle
POST /external-api/v1/actions/escalate-to-human
```

Suggested requests:

Send message:

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "message_text": "string"
}
```

Refund:

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "refund_pct": 30
}
```

Grant 3 free months:

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "months": 3
}
```

Grant bundle:

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "bundle_id": "B_1 | B_2 | B_3"
}
```

Cancel subscription:

```json
{
  "project_id": "string",
  "ticket_id": "string"
}
```

Success response:

```json
{
  "status": "ok",
  "external_action_id": "string"
}
```

Error response:

```json
{
  "status": "error",
  "error_code": "action_failed",
  "message": "external action failed"
}
```

If a critical outbound action fails, it must be treated as not completed and ticket should be escalated to human agent via `_escalate_to_human(escalated_on_error=true)`. 

### External Ticket Analytics API

This is the external API used by `TICKET_STATUS_SYNC_JOB` to retrieve delayed outcomes (CSAT scores and disputes) from Zendesk.

It provides:

- CSAT result for a ticket
- Dispute information for a ticket

**Base URL:** `https://zendesk-tickets-analytics-service-280090119036.europe-central2.run.app`

**Authentication:** All requests must include:

- `Content-Type: application/json`
- `TOKEN: <api_token>`

Example:

HTTP

```
TOKEN: Yk8J5VwzLQmZgS7dB1cN2rT8uXkP4eA9hF3mLs6Q
```

> **⚠️ CRITICAL LIMITATION (Timeout Prevention):** Due to the complex logic required to verify disputes, **no more than 150 tickets** should be analyzed in a single request.

---

#### 1. POST /api/v1/tickets/batch-metrics

Returns CSAT and dispute data for an explicit list of ticket IDs.

**Headers:**

- `Content-Type: application/json`

- `TOKEN: <api_token>`

**Request body:**

- `ticket_ids` — array of integer ticket ids.

_Example:_

JSON

```
{
  "ticket_ids": [10543, 99999, 10590]
}
```

**Response:** The endpoint returns a JSON object with results. Each result item corresponds to one requested ticket.

Expected fields per result item:

- `ticket_id` — integer ticket id

- `csat_score` — integer or null

- `disputes` — array

- `error` — optional string for per-ticket failure

- `message` — optional human-readable error description

_Example:_

JSON

```
{
  "results": [
    {
      "ticket_id": 10543,
      "csat_score": 1,
      "disputes": []
    },
    {
      "ticket_id": 99999,
      "error": "ticket_not_found",
      "message": "Ticket ID 99999 does not exist in the source system."
    },
    {
      "ticket_id": 10590,
      "csat_score": null,
      "disputes": [
        {
          "dispute_id": "DSP-101",
          "reason": "Chargeback",
          "status": "open"
        }
      ]
    }
  ]
}
```

**Operational rule:**

- Do not send more than 150 ticket IDs in one request.



---

#### HTTP Status Handling

Both endpoints return a normal HTTP status code for the whole request.

Expected handling:

- **200 OK** — request was processed successfully at the HTTP level; individual ticket-level errors may still exist inside results.

- **400 Bad Request** — invalid request format, missing required fields, or invalid JSON.

- **500 Internal Server Error** — server-side failure.

**The runtime must validate both:**

1. The HTTP status code.

2. The JSON response body.

A request must not be treated as successful only because the server returned `200 OK`. Per-ticket errors inside `results` must also be checked.

**Runtime integration rules:** `TICKET_STATUS_SYNC_JOB` uses this API to fetch delayed outcomes for previously closed tickets.