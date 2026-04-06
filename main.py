import os
import json
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import gradio as gr
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("--- STARTING MAIN.PY ---")
NEGOTIATOR_API_URL = os.getenv("NEGOTIATOR_API_URL", "http://127.0.0.1:8000/api/v1/inbound/messages")
NEGOTIATOR_INBOUND_TOKEN = os.getenv("NEGOTIATOR_INBOUND_BEARER_TOKEN", os.getenv("NEGOTIATOR_API_TOKEN", "ILrpza83rsmcBybmBzovM6N6Pb0djx1xVRCMYjFD2fc"))
NEGOTIATOR_OUTBOUND_TOKEN = os.getenv("NEGOTIATOR_OUTBOUND_BEARER_TOKEN", os.getenv("NEGOTIATOR_API_TOKEN", "ldHI5i88dssuGoacqDDSimNYLmhjZVcE7qGqQWSsMbo"))

print(f"API URL: {NEGOTIATOR_API_URL}")

app = FastAPI(title="Negotiator Playground Mock Server")

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != NEGOTIATOR_OUTBOUND_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

# Define shared state
# Keyed by ticket_id, value is a list of chat message dicts for Gradio Chatbot (type="messages")
chat_history: Dict[str, List[Dict[str, str]]] = {}

def get_history(ticket_id: str) -> List[Dict[str, str]]:
    if not ticket_id.strip():
        return []
    if ticket_id not in chat_history:
        chat_history[ticket_id] = []
    # Return a copy to ensure Gradio detects state changes
    return chat_history[ticket_id].copy()

def add_message(ticket_id: str, role: str, content: str, timestamp: bool = True):
    if not ticket_id.strip():
        return
        
    history = chat_history.get(ticket_id, [])
    
    if timestamp:
        current_time = datetime.now().strftime("%H:%M:%S")
        if role == "user":
            formatted_content = f"**User ({current_time}):**\n{content}"
            history.append({"role": "user", "content": formatted_content})
        elif role == "API Call":
            formatted_content = f"**API Call ({current_time}):**\n{content}"
            history.append({"role": "assistant", "content": formatted_content})
        else: # assistant
            formatted_content = f"**Assistant ({current_time}):**\n{content}"
            history.append({"role": "assistant", "content": formatted_content})
    else:
        history.append({"role": role, "content": content})
        
    chat_history[ticket_id] = history

# --- Pydantic Models for Webhooks ---
class SendMessageRequest(BaseModel):
    project_id: Optional[str] = None
    ticket_id: str
    message_text: str

class RefundRequest(BaseModel):
    project_id: Optional[str] = None
    ticket_id: str
    refund_pct: int

class GrantFreeMonthsRequest(BaseModel):
    project_id: Optional[str] = None
    ticket_id: str
    months: int

class GrantBundleRequest(BaseModel):
    project_id: Optional[str] = None
    ticket_id: str
    bundle_id: str

class CancelSubscriptionRequest(BaseModel):
    project_id: Optional[str] = None
    ticket_id: str

# --- FastAPI Webhook Endpoints ---

@app.post("/external-api/v1/messages/send", dependencies=[Depends(verify_token)])
async def mock_send_message(req: SendMessageRequest):
    add_message(req.ticket_id, "assistant", req.message_text)
    return {"status": "ok", "external_action_id": f"mock_msg_{int(time.time())}"}

@app.post("/external-api/v1/actions/refund", dependencies=[Depends(verify_token)])
async def mock_refund(req: RefundRequest):
    payload = {"refund_pct": req.refund_pct}
    add_message(req.ticket_id, "API Call", f"`POST /external-api/v1/actions/refund` | Payload: `{json.dumps(payload)}`")
    return {"status": "ok", "external_action_id": f"mock_refund_{int(time.time())}"}

@app.post("/external-api/v1/actions/grant-free-months", dependencies=[Depends(verify_token)])
async def mock_grant_free_months(req: GrantFreeMonthsRequest):
    payload = {"months": req.months}
    add_message(req.ticket_id, "API Call", f"`POST /external-api/v1/actions/grant-free-months` | Payload: `{json.dumps(payload)}`")
    return {"status": "ok", "external_action_id": f"mock_freemonths_{int(time.time())}"}

@app.post("/external-api/v1/actions/grant-bundle", dependencies=[Depends(verify_token)])
async def mock_grant_bundle(req: GrantBundleRequest):
    payload = {"bundle_id": req.bundle_id}
    add_message(req.ticket_id, "API Call", f"`POST /external-api/v1/actions/grant-bundle` | Payload: `{json.dumps(payload)}`")
    return {"status": "ok", "external_action_id": f"mock_bundle_{int(time.time())}"}

@app.post("/external-api/v1/actions/cancel-subscription", dependencies=[Depends(verify_token)])
async def mock_cancel_subscription(req: CancelSubscriptionRequest):
    add_message(req.ticket_id, "API Call", "`POST /external-api/v1/actions/cancel-subscription` | Payload: `{}`")
    return {"status": "ok", "external_action_id": f"mock_cancel_{int(time.time())}"}

@app.post("/external-api/v1/actions/escalate-to-human", dependencies=[Depends(verify_token)])
async def mock_escalate(request: Request):
    try:
        payload = await request.json()
    except:
        payload = {}
    ticket_id = payload.get("ticket_id", "unknown_ticket")
    add_message(ticket_id, "API Call", f"`POST /external-api/v1/actions/escalate-to-human` | Payload: `{json.dumps(payload)}`")
    return {"status": "ok", "external_action_id": f"mock_escalate_{int(time.time())}"}

# --- Gradio UI ---

DEFAULT_PAYMENT_DATA = """Renewable Subscription:
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
---"""

def ui_send_message(user_text, ticket_id, payment_data_str):
    if not user_text.strip() or not ticket_id.strip():
        return "", get_history(ticket_id)
        
    # Append user message immediately
    add_message(ticket_id, "user", user_text)
    
    try:
        payment_dict = json.loads(payment_data_str)
    except json.JSONDecodeError:
        payment_dict = {"raw_text": payment_data_str}

    payload = {
        "project_id": "test_project",
        "ticket_id": ticket_id,
        "message_text": user_text,
        "payment_data": payment_dict,
        "metadata": {}
    }
    
    headers = {
        "Authorization": f"Bearer {NEGOTIATOR_INBOUND_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Run POST request synchronously (Gradio runs this in a thread pool)
    try:
        resp = requests.post(NEGOTIATOR_API_URL, json=payload, headers=headers, timeout=10.0)
        if resp.status_code != 200:
            add_message(ticket_id, "API Call", f"🚨 Backend Error {resp.status_code}: {resp.text}")
    except Exception as e:
        add_message(ticket_id, "API Call", f"🚨 Request failed: {str(e)}")
        
    return "", get_history(ticket_id)

def refresh_chat(ticket_id):
    history = get_history(ticket_id)
    return history

with gr.Blocks(title="Playground Testing Tool") as demo:
    gr.Markdown("# 🧪 Negotiator Playground Testing Tool")
    
    with gr.Row():
        with gr.Column(scale=1):
            ticket_input = gr.Textbox(label="Ticket ID", value="TEST-12345")
            payment_input = gr.TextArea(label="Payment Data", value=DEFAULT_PAYMENT_DATA, lines=15)
            
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Negotiation Flow", height=600)
            with gr.Row():
                msg_input = gr.Textbox(label="Type your message...", show_label=False, scale=4)
                send_btn = gr.Button("Send", variant="primary", scale=1)
                
            # Timer to refresh chat for incoming webhooks (refreshes every 1.5s)
            timer = gr.Timer(value=1.5, active=True)
            
    # Actions
    send_action = msg_input.submit(
        fn=ui_send_message, 
        inputs=[msg_input, ticket_input, payment_input], 
        outputs=[msg_input, chatbot]
    )
    send_btn.click(
        fn=ui_send_message, 
        inputs=[msg_input, ticket_input, payment_input], 
        outputs=[msg_input, chatbot]
    )
    
    timer.tick(
        fn=refresh_chat,
        inputs=[ticket_input],
        outputs=[chatbot]
    )

# Mount Gradio app to FastAPI server
# Since this goes into the root, it handles GET /
print("--- MOUNTING GRADIO ---")
gradio_app = gr.mount_gradio_app(app, demo, path="/")
print("--- GRADIO MOUNTED ---")
