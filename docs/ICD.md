# Interface Control Document (ICD) – Playground Testing API

## Introduction

This document defines the strictly API-based integration contract for the **Playground Testing Tool**. 

The testing application does not require database access. Instead, it operates entirely via two API layers:
1. **Outbound Action API (Hosted by the UI / Tester):** A local mock server that listens for backend webhooks to receive AI text responses and system tool calls.
2. **Inbound API (Hosted by the Backend):** The main Negotiator entry point where the tester submits synthetic customer messages.

---

## 1. Outbound Action API (UI-Hosted Mock Server)

This is the **external API** that the Negotiator backend calls when it needs to send a response to the user or execute an external business action. 

For the Playground Tool, **these endpoints must be hosted locally** (e.g., via FastAPI). When the backend processes an inbound message, it will asynchronously trigger these endpoints. The UI must intercept these requests, display them in the chat interface chronologically, and always return a success response to satisfy the backend.

### Authentication

The backend will send requests with a Bearer token. Your local server should expect and validate this header (defined as `NEGOTIATOR_OUTBOUND_BEARER_TOKEN`):

```http
Authorization: Bearer <token>
```

### Endpoints & Request Payloads

The local server must expose the following `POST` endpoints.

**1. Send message (AI Text Response):**
```http
POST /external-api/v1/messages/send
```
```json
{
  "project_id": "string",
  "ticket_id": "string",
  "message_text": "string"
}
```

**2. Refund Action:**
```http
POST /external-api/v1/actions/refund
```
```json
{
  "project_id": "string",
  "ticket_id": "string",
  "refund_pct": 30
}
```

**3. Grant 3 Free Months Action:**
```http
POST /external-api/v1/actions/grant-free-months
```
```json
{
  "project_id": "string",
  "ticket_id": "string",
  "months": 3
}
```

**4. Grant Bundle Action:**
```http
POST /external-api/v1/actions/grant-bundle
```
```json
{
  "project_id": "string",
  "ticket_id": "string",
  "bundle_id": "B_1 | B_2 | B_3"
}
```

**5. Cancel Subscription Action:**
```http
POST /external-api/v1/actions/cancel-subscription
```
```json
{
  "project_id": "string",
  "ticket_id": "string"
}
```

**6. Escalate to Human Action:**
```http
POST /external-api/v1/actions/escalate-to-human
```
*(Payload varies but will include at least `ticket_id` and `project_id`).*

### Expected Responses from the UI Server

For the Playground to function smoothly, your mock endpoints should always accept the action and return a success response:

**Success Response (HTTP 200 OK):**
```json
{
  "status": "ok",
  "external_action_id": "mock_id_12345"
}
```

*(Note: If testing error-handling scenarios in the backend, you can configure your mock server to occasionally return the following error response).*

**Error Response (HTTP 400/500):**
```json
{
  "status": "error",
  "error_code": "action_failed",
  "message": "external action failed"
}
```

---

## 2. Inbound API (Backend Endpoint)

This is the main entry point hosted by the Negotiator backend. The Playground UI uses this endpoint to submit tester messages, initiating or continuing the negotiation.

### Authentication

The Playground Tool must send requests with the configured Bearer token (defined as `NEGOTIATOR_INBOUND_BEARER_TOKEN`):

```http
Authorization: Bearer <token>
```

### Endpoint

```http
POST /api/v1/inbound/messages
```

**Purpose:**
- Submit a new user message.
- Provide the static `payment_data` context required for the AI's decision-making.
- Trigger backend asynchronous processing (which will eventually call your Outbound Action API).

### Request Body

```json
{
  "project_id": "string",
  "ticket_id": "string",
  "message_text": "string",
  "payment_data": {},
  "metadata": {}
}
```

**Field Rules:**
- `ticket_id` (required): A string assigned by the tester in the UI. Reusing a `ticket_id` continues an existing conversation context.
- `message_text` (required): The actual chat message typed by the tester. Must be a non-empty string.
- `payment_data` (required): A valid JSON object representing the billing context. The UI must inject this automatically based on the tester's settings.
- `project_id` (optional): Allowed, but currently ignored by decision logic in v1.
- `metadata` (optional): Defaults to `{}`.

### Standard Responses

**Success (HTTP 200 OK):**
Indicates the message was accepted and queued for processing.
```json
{
  "status": "ok",
  "error_code": null,
  "message": null
}
```

**Validation Error (HTTP 400 Bad Request):**
Indicates malformed payload (e.g., missing `payment_data`).
```json
{
  "detail": {
    "status": "error",
    "error_code": "validation_error",
    "message": "payment_data is required and message_text must be non-empty"
  }
}
```

**Conflict / Lifecycle Rejection (HTTP 409 Conflict):**
Indicates you are trying to send a message to a ticket that has already been finalized and escalated.
```json
{
  "detail": {
    "status": "error",
    "error_code": "ticket_finalized_and_already_escalated",
    "message": "This ticket is finalized and already routed to human support."
  }
}
```