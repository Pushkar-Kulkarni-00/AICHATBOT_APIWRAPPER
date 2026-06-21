# QuickCommerce AI - Complete Reference

## Architecture Overview

```
┌─ React Frontend (Port 5173)
│  ├─ Support Intent Selection (Welcome Screen)
│  ├─ Guided Workflow Navigation
│  └─ Real-time Chat with Streaming
│
├─ FastAPI Backend (Port 8000)
│  ├─ Policy Engine (Business Rules)
│  ├─ Knowledge Base (RAG Policies)
│  ├─ Workflow Engine (Intent Management)
│  └─ LLM Integration (Ollama Phi)
│
└─ Ollama Local LLM (Port 11434)
   └─ Phi 3.5 / LLaMA 3.2 Models
```

---

## API Endpoints

### 1. GET `/api/models`
**Returns available LLM models**
```json
{
  "models": {
    "phi3.5": "Phi 3.5",
    "llama3.2:3b": "LLaMA 3.2 3B"
  }
}
```

### 2. GET `/api/support-intents`
**Returns all support intent options for UI**
```json
{
  "intents": [
    {
      "code": "ORDER_STATUS",
      "name": "Check Order Status",
      "icon": "📦"
    },
    {
      "code": "RETURN_REQUEST",
      "name": "Return or Refund Request",
      "icon": "↩️"
    }
    // ... 11 more intents
  ]
}
```

### 3. POST `/api/support-intent`
**Trigger specific intent workflow**
```json
REQUEST:
{
  "intent": "RETURN_REQUEST",
  "order_id": "ORD12345" (optional)
}

RESPONSE:
{
  "success": true,
  "intent": "RETURN_REQUEST",
  "initial_message": "I'll help you with a return. Please provide your Order ID",
  "requires_order_id": true,
  "follow_up_questions": [
    "What is the reason for return?",
    "Is the item still in original packaging?"
  ]
}
```

### 4. GET `/api/order/{order_id}`
**Retrieve specific order details**
```json
REQUEST: /api/order/ORD12345

RESPONSE:
{
  "success": true,
  "order": {
    "order_id": "ORD12345",
    "status": "out_for_delivery",
    "items": [...],
    "total": 12.99,
    "estimated_delivery": "2024-01-18",
    "tracking_number": "TRK9876543"
  },
  "message": "Your order is out for delivery and should arrive today."
}
```

### 5. POST `/api/chat`
**Stream chat responses with policy context**
```json
REQUEST:
{
  "message": "My package is damaged",
  "model": "phi3.5",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "intent": "DAMAGED_ITEM",
  "order_id": "ORD12346",
  "file_context": null,
  "file_type": null
}

RESPONSE (streaming):
Text chunks stream real-time as they're generated
```

### 6. POST `/api/upload`
**Upload files for context**
```json
REQUEST: multipart/form-data with file

RESPONSE:
{
  "success": true,
  "file_type": "image" | "text",
  "file_context": "base64_or_text_content",
  "filename": "receipt.jpg"
}

Supported: PDF, TXT, CSV, DOCX, PNG, JPG, JPEG
```

### 7. GET `/health`
**Health check**
```json
{
  "status": "ok"
}
```

---

## Frontend Data Flow

### Initial State
```
App starts
  ↓
Fetch /api/models → Display model dropdown
  ↓
Fetch /api/support-intents → Display support cards
  ↓
User sees welcome screen with 13 buttons
```

### After Intent Selection
```
User clicks button (e.g., "RETURN_REQUEST")
  ↓
POST /api/support-intent
  ↓
Get initial_message & workflow info
  ↓
Display bot message
  ↓
Show input field
  ↓
User types answer
  ↓
POST /api/chat with intent context
  ↓
Stream response (with policies applied)
```

### Chat Loop
```
While conversation ongoing:
  User types → POST /api/chat
    ↓
  Backend applies policy engine
    ↓
  RAG searches knowledge base
    ↓
  LLM generates response with context
    ↓
  Stream to frontend
    ↓
  Display message
```

---

## Backend Processing

### Chat Request Processing

1. **Initialize History**
   - Add system message with intent-specific policies
   - Add file context if uploaded
   - Rebuild message history from frontend

2. **Fetch Order Context** (if order_id provided)
   - Lookup in `mock_inventory.json`
   - Include order details in system prompt

3. **Build System Prompt**
   - Include relevant policies
   - Add order context
   - Set professional tone
   - Enforce safety rules

4. **Stream LLM Response**
   - Call Ollama API
   - Stream chunks as they arrive
   - Return as Server-Sent Events

Example system prompt:
```
You are a professional customer service AI for a quick-commerce platform.

INTENT: Return or Refund Request

RELEVANT POLICIES:
RETURN_POLICY:
- Non-perishable items: Returnable within 30 days if unopened
- Perishable items: NOT returnable after delivery
[... more policies ...]

RULES:
1. NEVER invent order status or tracking information
2. NEVER invent tax percentages
3. If information is unavailable, explicitly say "I don't have this information"
[... more rules ...]

ORDER CONTEXT:
{order_id: "ORD12345", status: "delivered", items: [...]}
```

---

## Policy Engine Rules

### Return Eligibility Check
```python
def check_return_eligibility(order):
    # Check order age (max 30 days)
    # Check item type (perishable = ineligible)
    # Check condition (damaged = 7 days, special handling)
    # Return: {eligible, reason, options, window_days}
```

### Perishable Detection
```python
def is_perishable(item_name):
    categories = [
        "frozen_products", "fresh_produce", "dairy",
        "meat", "seafood", "baked_goods"
    ]
    # Returns True if item matches any category
```

### Shipping Restrictions
```python
def check_shipping_restrictions(country, item_type):
    # Check if item restricted to country
    # Return: {restricted: bool, reason: str}
    # Examples:
    # - Japan restricts dairy, fresh produce
    # - Australia restricts any perishable
```

### Tax Info Lookup
```python
def get_tax_info(country):
    # Return tax rate, customs rules, delivery days
    # If country not found: explicit "I don't have this info"
```

---

## Knowledge Base Search

The knowledge base contains 10 policy documents:

1. **return_policy** - All return rules
2. **shipping_policy** - Shipping timelines
3. **perishable_items** - Perishable definitions
4. **tax_and_customs** - Tax by country
5. **international_shipping** - International rules
6. **order_status** - Status definitions
7. **damaged_items** - Damage claim process
8. **missing_items** - Missing item policy
9. **cancellation_policy** - When you can cancel
10. **payment_issues** - Payment problem resolution

**RAG Search Logic:**
```
User question → keyword extraction
             → match against policy keywords
             → retrieve relevant documents
             → inject into system prompt
             → LLM generates response with context
```

---

## Mock Inventory Structure

```json
{
  "orders": {
    "ORD12345": {
      "order_id": "ORD12345",
      "status": "out_for_delivery",
      "items": [{name, type, quantity, price, condition}],
      "shipping_address": "...",
      "estimated_delivery": "...",
      "returnable": true/false
    }
  },
  "countries": {
    "USA": {
      "tax_rate": "varies by state",
      "customs_rules": "...",
      "delivery_days": 2,
      "hazardous_restrictions": []
    }
  },
  "perishable_items": ["fresh_produce", "frozen_products", ...],
  "return_policies": {...}
}
```

---

## Workflow Definitions

Each intent has:
- **icon** - Emoji for UI
- **initial_message** - Bot's first message
- **requires_order_id** - Whether to ask for order ID
- **follow_up_questions** - List of potential follow-ups
- **workflow_steps** - Backend steps to execute

Example: RETURN_REQUEST
```python
{
  "name": "Return or Refund Request",
  "icon": "↩️",
  "initial_message": "I'll help you with a return. Please provide your Order ID",
  "requires_order_id": True,
  "follow_up_questions": [
    "What is the reason for return?",
    "Is the item still in original packaging?"
  ],
  "workflow_steps": [
    "Get order ID",
    "Check return eligibility",
    "Ask reason and condition",
    "Provide return instructions",
    "Issue RMA number if eligible"
  ]
}
```

---

## Error Handling

### Rate Limiting (429)
```
If Ollama rate limits:
Response: "[Rate limited, please try again]"
User can retry after brief wait
```

### Invalid Order
```
Request: /api/order/NONEXISTENT
Response: HTTPException 404
Frontend: "Order not found"
```

### Network Issues
```
If can't reach Ollama:
Response: "[Error: Connection failed]"
Frontend: Shows error message
User: Instructed to check Ollama is running
```

---

## Environment Variables

### Backend (.env)
```
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=phi3.5
API_HOST=0.0.0.0
API_PORT=8000
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=500
```

### Frontend (.env.local)
```
VITE_API_URL=http://localhost:8000
```

---

## Performance Notes

- **Ollama response time**: 10-30 seconds (depends on model)
- **RAG search**: <100ms (in-memory)
- **Policy engine checks**: <10ms
- **Streaming**: Real-time chunks, no batching needed
- **Memory**: ~500MB for Phi model

---

## Security Considerations

✅ **No PII stored** - All data in mock JSON
✅ **No authentication** - Placeholder for future
✅ **CORS enabled** - Localhost only in dev
✅ **No API keys exposed** - Ollama is local
✅ **Input validation** - Pydantic models check types
✅ **Error messages** - Safe, don't reveal internals

---

## Testing Checklist

- [ ] Backend starts on :8000
- [ ] Ollama responds on :11434
- [ ] Frontend starts on :5173
- [ ] Support cards display (13 buttons)
- [ ] ORDER_STATUS intent retrieves ORD12345
- [ ] RETURN_REQUEST checks eligibility correctly
- [ ] TAX_CUSTOMS shows country info
- [ ] File upload works (PDF, image)
- [ ] Streaming chat displays in real-time
- [ ] Back button resets to welcome screen
