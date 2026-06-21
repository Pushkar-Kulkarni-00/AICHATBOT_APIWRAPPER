from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from pypdf import PdfReader
import json
import os
import base64
import io
import csv
import docx as docx_lib
import re
from typing import Optional, List
from pathlib import Path

from policy_engine import PolicyEngine
from knowledge_base import KnowledgeBase
from workflows import WorkflowEngine

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
policy_engine = PolicyEngine()
knowledge_base = KnowledgeBase()
workflow_engine = WorkflowEngine(policy_engine, knowledge_base)

# ============= Helper Functions =============

def extract_order_id(message):
    """Extract order ID from user message (pattern: ORDxxxxx)"""
    match = re.search(r'ORD\d+', message)
    return match.group(0) if match else None

# Initialize LLM
def get_llm(model_name):
    return ChatOpenAI(
        openai_api_base="http://localhost:11434/v1",
        openai_api_key="ollama",
        model_name=model_name,
        temperature=0.5,
        max_tokens=500,
        streaming=True,
    )

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    model: str = "phi3.5"
    history: list = []
    file_context: Optional[str] = None
    file_type: Optional[str] = None
    intent: Optional[str] = None
    order_id: Optional[str] = None

class SupportIntentRequest(BaseModel):
    intent: str
    order_id: Optional[str] = None

class OrderQueryRequest(BaseModel):
    order_id: str

# ============= API Endpoints =============

@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {
        "models": {
            "phi3.5": "Phi 3.5",
            "llama3.2:3b": "LLaMA 3.2 3B",
        }
    }

@app.get("/api/support-intents")
async def get_support_intents():
    """Get all available support intents"""
    intents = []
    for code, name, icon in workflow_engine.all_intents():
        intents.append({
            "code": code,
            "name": name,
            "icon": icon
        })
    return {"intents": intents}

@app.get("/api/order/{order_id}")
async def get_order(order_id: str):
    """Get order details from mock inventory"""
    orders = policy_engine.data["orders"]
    order = orders.get(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "success": True,
        "order": policy_engine.validate_order_status(order),
        "message": policy_engine.get_delivery_status_message(order)
    }

@app.post("/api/support-intent")
async def send_support_intent(request: SupportIntentRequest):
    """Receive a predefined support intent"""
    intent_details = workflow_engine.get_intent_details(request.intent)
    
    if not intent_details:
        raise HTTPException(status_code=400, detail="Invalid intent")
    
    initial_message = workflow_engine.get_initial_message(request.intent)
    
    return {
        "success": True,
        "intent": request.intent,
        "initial_message": initial_message,
        "requires_order_id": intent_details.get("requires_order_id", False),
        "follow_up_questions": intent_details.get("follow_up_questions", [])
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream chat response with policy engine context"""
    try:
        llm = get_llm(request.model)
        history = []

        # Build system prompt with intent-specific policies
        if request.intent:
            order_context = ""
            
            # Try to get order_id from request or extract from message
            order_id = request.order_id
            if not order_id and request.intent:
                # Check if this intent requires order_id
                intent_details = workflow_engine.get_intent_details(request.intent)
                if intent_details and intent_details.get("requires_order_id"):
                    # Extract order ID from user's message
                    order_id = extract_order_id(request.message)
            
            # Fetch order context if we have an order_id
            if order_id:
                orders = policy_engine.data["orders"]
                if order_id in orders:
                    order_context = f"\n\nORDER CONTEXT:\n{json.dumps(orders[order_id], indent=2)}"
            
            system_prompt = workflow_engine.build_system_prompt(request.intent, order_context)
        else:
            system_prompt = "You are a professional customer service AI. Be helpful, concise, and empathetic."

        history.append(SystemMessage(content=system_prompt))

        # Add file context if uploaded
        if request.file_type == "text" and request.file_context:
            history.append(SystemMessage(content=f"Uploaded file context:\n{request.file_context}"))

        # Build message history
        if request.history:
            for msg in request.history:
                try:
                    if isinstance(msg, dict):
                        role = msg.get("role")
                        content = msg.get("content", "")
                        
                        if role == "user":
                            history.append(HumanMessage(content=content))
                        elif role == "assistant":
                            history.append(AIMessage(content=content))
                except Exception:
                    pass

        # Add current message
        if request.file_type == "image" and request.file_context:
            try:
                b64, media_type = request.file_context.split("|")
                history.append(HumanMessage(content=[
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                    {"type": "text", "text": request.message}
                ]))
            except Exception:
                history.append(HumanMessage(content=request.message))
        else:
            history.append(HumanMessage(content=request.message))

        async def generate():
            try:
                stream = llm.stream(history)
                for chunk in stream:
                    if chunk.content:
                        yield chunk.content
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    yield "\n[Rate limited, please try again]"
                else:
                    yield f"\n[Error: {error_msg}]"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    try:
        content = await file.read()
        name = file.filename.lower()

        if name.endswith((".png", ".jpg", ".jpeg")):
            b64 = base64.b64encode(content).decode()
            ext = name.split(".")[-1]
            media_type = f"image/{'jpeg' if ext == 'jpg' else ext}"
            return {
                "success": True,
                "file_type": "image",
                "file_context": f"{b64}|{media_type}",
                "filename": file.filename
            }
        else:
            text = extract_text_from_file(content, name)
            if text is None:
                raise Exception("Unsupported file type")
            return {
                "success": True,
                "file_type": "text",
                "file_context": f"File: {file.filename}\n\n{text}",
                "filename": file.filename
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}

# ============= Helper Functions =============

def extract_text_from_file(file_content, filename):
    """Extract text from various file types"""
    name = filename.lower()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text[:12000]

    elif name.endswith(".txt"):
        return file_content.decode("utf-8", errors="ignore")[:12000]

    elif name.endswith(".csv"):
        content = file_content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(content))
        rows = []
        for i, row in enumerate(reader):
            rows.append(", ".join(row))
            if i > 200:
                rows.append("... (truncated)")
                break
        return "\n".join(rows)

    elif name.endswith(".docx"):
        doc = docx_lib.Document(io.BytesIO(file_content))
        text = "\n".join([p.text for p in doc.paragraphs])
        return text[:12000]

    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)