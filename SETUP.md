# QuickCommerce AI Customer Service - Setup Guide

## Project Structure
```
quickcommerce-ai/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── policy_engine.py        # Rules & policies
│   ├── knowledge_base.py       # RAG knowledge store
│   ├── workflows.py            # Support workflows
│   ├── mock_inventory.json     # Mock order/inventory data
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── App.css             # Styling
│   │   ├── components/
│   │   │   ├── SupportCards.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   └── WorkflowPanel.jsx
│   │   └── index.js
│   ├── package.json
│   └── .env.local              # VITE_API_URL=http://localhost:8000
└── SETUP.md                    # This file

## Prerequisites
- Python 3.10+
- Node.js 16+
- Ollama running locally (http://localhost:11434)

## Installation & Running

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Server runs on http://localhost:8000

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
App runs on http://localhost:5173

### 3. Verify Ollama
```bash
curl http://localhost:11434/api/tags
```
Should return available models (phi3.5, llama3.2:3b)

## Key Features
- **Guided Support Flows**: Users click predefined buttons before typing
- **Policy Engine**: Rule-based responses for returns, shipping, taxes
- **RAG Pipeline**: Retrieves policies before generating responses
- **Mock Data**: No database needed - uses JSON files
- **Streaming Responses**: Real-time chat streaming

## API Endpoints
- `POST /api/chat` - Stream chat responses
- `POST /api/upload` - Upload files
- `POST /api/support-intent` - Send predefined intent
- `GET /api/order/{order_id}` - Get order details
- `GET /api/models` - List available models
- `GET /health` - Health check

## Support Intents
- `ORDER_STATUS` - Check order
- `DELIVERY_TRACKING` - Track package
- `RETURN_REQUEST` - Request return
- `CANCEL_ORDER` - Cancel order
- `DELIVERY_DELAY` - Report delay
- `DAMAGED_ITEM` - Report damage
- `MISSING_ITEM` - Report missing item
- `TAX_CUSTOMS` - Tax/customs info
- `PAYMENT_ISSUE` - Payment problem
- `OTHER` - Free-form question

## Workflow Examples
Each intent triggers a guided conversation:
- **RETURN_REQUEST**: Asks for reason → checks eligibility → processes
- **ORDER_STATUS**: Asks for order ID → retrieves status → provides tracking
- **DELIVERY_DELAY**: Asks for order ID → checks status → provides ETA

## Testing
```bash
# Test order status
curl -X POST http://localhost:8000/api/support-intent \
  -H "Content-Type: application/json" \
  -d '{"intent": "ORDER_STATUS", "user_message": "ORD12345"}'
```

## Troubleshooting
- **No Ollama connection**: Start Ollama with `ollama serve`
- **CORS errors**: Check backend CORS config in main.py
- **Missing models**: Pull with `ollama pull phi3.5`
- **Port conflicts**: Change port in main.py (line ~190)

## Customization
- Add policies to `backend/knowledge_base.py`
- Add workflows to `backend/workflows.py`
- Modify UI in `frontend/src/components/`
- Add intents in `workflows.py` and update frontend
