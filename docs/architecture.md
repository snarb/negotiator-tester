# Playground Testing Tool Specification

## Overview

An interactive UI application built to simulate and test conversational flows with the Negotiator backend. The interface mimics the OpenAI Playground experience, displaying both text responses and internal tool calls in a single chronological chat stream.

**Crucial Architecture Note:** This tool operates entirely via API communication. It does not read from or write to any database. 
* It **sends** user messages to the backend via the public Inbound API.
* It **receives** AI responses and tool executions via a locally hosted FastAPI server acting as a webhook receiver (Outbound Action API).

---

## Technical Stack

* **UI Frontend:** Gradio (using the Chatbot component with conversational history support).
* **Local Webhook Server:** FastAPI (hosted alongside the UI to intercept backend callbacks and push them to the chat interface).

---

## Requirements & Features

### 1. Chat Interface (Chronological Stream)

The main window is a Gradio Chatbot component that displays three types of events in strict chronological order (with timestamps):

* **User:** Messages sent by the tester via the text input field.
* **API Call:** System actions and tool executions intercepted by the local FastAPI server (e.g., `REFUND`, `GRANT_BUNDLE`). These must be visually distinct from regular messages.
* **Assistant:** Text responses from the AI, received via the local FastAPI server's send-message endpoint.

**Example UI Display:**
> **User (13:08:06):** I want a refund.
> **API Call (13:08:08):** `POST /external-api/v1/actions/refund` | Payload: `{"refund_pct": 100}`
> **Assistant (13:08:10):** Done. I have issued a refund.

### 2. Session Context (`ticket_id` & `payment_data`)

A side panel must be available to configure the session context before and during the chat:

* **`ticket_id`:** A text input to define the current session ID. This allows testers to start fresh dialogues or test reopen logic by reusing a known ID.
* **`payment_data`:** A text area for the payment context. **This data is set once and sent automatically with every user message.** It must default to the following text (the UI must wrap this string into a valid JSON object, as required by the Inbound API, before sending):

```text
Renewable Subscription:
---
Status: cancelled (but you'll keep access until the end of the current billing period)
Description: 1-week trial at 22.99 GBP, followed by a monthly plan at 74.99 GBP
Cancelled at: Nov 01, 2025

Recent Payments:
Monthly rebill on Oct 09, 2025:
        - Status: failed
        - Payment method: ApplePay
        - Amount: 74.99 GBP
Trial payment on Sep 09, 2025:
        - Status: paid
        - Payment method: ApplePay
        - Amount: 22.99 GBP
---
Upsale (Stress and Anxiety Relief Toolkit) - latest payment to refund:
---
Status: paid
Payment method: ApplePay
Amount: 29.99 GBP
Created at: Oct 09, 2025
---
```

### 3. Sending Messages (To Backend Inbound API)

When the tester sends a message, the application makes a `POST` request to the `NEGOTIATOR_API_URL`.
* **Payload:** Includes `message_text` (from chat input), `ticket_id` (from side panel), and `payment_data` (from side panel).
* **Auth:** Uses Bearer token authentication from the `.env` file.

### 4. Receiving Responses & Actions (Local Outbound Action API)

The tool must run a local FastAPI server to intercept webhooks from the Negotiator backend. Whenever an endpoint is hit by the backend, the event is immediately pushed to the Gradio UI chat stream.

The server must mock the following endpoints, require `Authorization: Bearer <token>`, and always return a success response (`{"status": "ok", "external_action_id": "mock_id"}`):

* **Receive AI Text Response:**
    * `POST /external-api/v1/messages/send`
    * *Action:* Renders as an **Assistant** message in the UI using the `message_text` from the received payload.
* **Intercept Tool Calls (Actions):**
    * `POST /external-api/v1/actions/refund`
    * `POST /external-api/v1/actions/cancel-subscription`
    * `POST /external-api/v1/actions/grant-free-months`
    * `POST /external-api/v1/actions/grant-bundle`
    * `POST /external-api/v1/actions/escalate-to-human`
    * *Action:* Renders as an **API Call** in the UI, displaying the specific endpoint name and its parsed JSON arguments (e.g., `refund_pct`, `months`, `bundle_id`).

### 5. Configuration

Environment variables must be stored locally in a `.env` file. No database paths are required.

```env
NEGOTIATOR_API_URL="http://127.0.0.1:8000/api/v1/inbound/messages"
NEGOTIATOR_INBOUND_BEARER_TOKEN="ILrpza83rsmcBybmBzovM6N6Pb0djx1xVRCMYjFD2fc"
NEGOTIATOR_OUTBOUND_BASE_URL="http://localhost:3000/external-api/v1"
NEGOTIATOR_OUTBOUND_BEARER_TOKEN="ldHI5i88dssuGoacqDDSimNYLmhjZVcE7qGqQWSsMbo"
```