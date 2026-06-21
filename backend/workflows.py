"""
Support workflow definitions for each intent
"""

SUPPORT_INTENTS = {
    "ORDER_STATUS": {
        "name": "Check Order Status",
        "icon": "📦",
        "initial_message": "Please provide your Order ID (e.g., ORD12345)",
        "requires_order_id": True,
        "workflow_steps": [
            "Request order ID",
            "Retrieve order details",
            "Display status and tracking",
            "Offer related help options"
        ]
    },
    "DELIVERY_TRACKING": {
        "name": "Track My Delivery",
        "icon": "🚚",
        "initial_message": "Please provide your Order ID to track your delivery",
        "requires_order_id": True,
        "workflow_steps": [
            "Request order ID",
            "Get tracking number",
            "Display current location/status",
            "Provide estimated delivery"
        ]
    },
    "RETURN_REQUEST": {
        "name": "Return or Refund Request",
        "icon": "↩️",
        "initial_message": "I'll help you with a return. Please provide your Order ID",
        "requires_order_id": True,
        "follow_up_questions": [
            "What is the reason for return?",
            "Is the item still in original packaging?",
            "What condition is the item in?"
        ],
        "workflow_steps": [
            "Get order ID",
            "Check return eligibility",
            "Ask reason and condition",
            "Provide return instructions",
            "Issue RMA number if eligible"
        ]
    },
    "CANCEL_ORDER": {
        "name": "Cancel My Order",
        "icon": "❌",
        "initial_message": "Please provide your Order ID to check cancellation eligibility",
        "requires_order_id": True,
        "workflow_steps": [
            "Get order ID",
            "Check if still in processing status",
            "Process cancellation if eligible",
            "Issue refund confirmation"
        ]
    },
    "DELIVERY_DELAY": {
        "name": "Delivery Delay Issue",
        "icon": "⏰",
        "initial_message": "Sorry for the delay. Please provide your Order ID",
        "requires_order_id": True,
        "workflow_steps": [
            "Get order ID",
            "Check current status",
            "Provide updated ETA",
            "Offer compensation or support"
        ]
    },
    "DAMAGED_ITEM": {
        "name": "Damaged Item Received",
        "icon": "💔",
        "initial_message": "I'm sorry to hear that. Please provide your Order ID",
        "requires_order_id": True,
        "follow_up_questions": [
            "Can you describe the damage?",
            "Do you have photos?",
            "Would you prefer replacement or refund?"
        ],
        "workflow_steps": [
            "Get order ID",
            "Document damage details",
            "Request photos if possible",
            "Arrange replacement or refund",
            "Issue return label"
        ]
    },
    "MISSING_ITEM": {
        "name": "Missing Item in Order",
        "icon": "🔍",
        "initial_message": "Let me help find your missing item. Please provide your Order ID",
        "requires_order_id": True,
        "follow_up_questions": [
            "Which item is missing?",
            "What was the item price?",
            "Did you check the package thoroughly?"
        ],
        "workflow_steps": [
            "Get order ID",
            "Identify missing item",
            "Check order manifest",
            "Process claim for refund or replacement"
        ]
    },
    "TAX_CUSTOMS": {
        "name": "Tax and Customs Information",
        "icon": "🌍",
        "initial_message": "Which country's tax/customs info do you need?",
        "requires_order_id": False,
        "follow_up_questions": [
            "What is the destination country?"
        ],
        "workflow_steps": [
            "Get destination country",
            "Provide tax rate info",
            "Explain customs process",
            "Note import restrictions if any"
        ]
    },
    "INTERNATIONAL_SHIPPING": {
        "name": "International Shipping Questions",
        "icon": "✈️",
        "initial_message": "What is your destination country?",
        "requires_order_id": False,
        "follow_up_questions": [
            "What country are you shipping to?",
            "What type of items?"
        ],
        "workflow_steps": [
            "Get destination country",
            "Check restrictions",
            "Provide delivery timeline",
            "Explain customs and duties"
        ]
    },
    "PERISHABLE_PRODUCT": {
        "name": "Product Storage and Perishability",
        "icon": "❄️",
        "initial_message": "What perishable item do you have a question about?",
        "requires_order_id": False,
        "follow_up_questions": [
            "What is the product?",
            "Do you have questions about storage or return?"
        ],
        "workflow_steps": [
            "Identify perishable product",
            "Explain storage requirements",
            "Clarify return/refund policy for perishables",
            "Provide expiration/freshness info if available"
        ]
    },
    "PAYMENT_ISSUE": {
        "name": "Payment Issue",
        "icon": "💳",
        "initial_message": "I'll help with your payment issue. Can you describe what happened?",
        "requires_order_id": False,
        "follow_up_questions": [
            "Were you charged twice?",
            "Did the transaction fail?",
            "Is the charge showing as pending?"
        ],
        "workflow_steps": [
            "Get issue description",
            "Check order record",
            "Verify with payment processor if needed",
            "Escalate to human agent for resolution"
        ]
    },
    "OTHER": {
        "name": "Other (Please Specify)",
        "icon": "💬",
        "initial_message": "Please describe your issue or question",
        "requires_order_id": False,
        "workflow_steps": [
            "Collect free-form question",
            "Route to general support",
            "Escalate to human if needed"
        ]
    }
}

class WorkflowEngine:
    def __init__(self, policy_engine, knowledge_base):
        self.intents = SUPPORT_INTENTS
        self.policy_engine = policy_engine
        self.knowledge_base = knowledge_base

    def get_intent_details(self, intent_code):
        """Get workflow details for an intent"""
        return self.intents.get(intent_code, None)

    def get_initial_message(self, intent_code):
        """Get the first message for an intent"""
        intent = self.intents.get(intent_code)
        return intent["initial_message"] if intent else "How can we help?"

    def get_follow_up_questions(self, intent_code):
        """Get follow-up questions for an intent"""
        intent = self.intents.get(intent_code)
        return intent.get("follow_up_questions", [])

    def route_to_human(self, reason):
        """Check if issue should be escalated"""
        escalation_reasons = [
            "value_exceeds_500",
            "fraud_suspected",
            "legal_claim",
            "multiple_failures",
            "safety_concern",
            "payment_issue_unresolved"
        ]
        return reason in escalation_reasons

    def build_system_prompt(self, intent_code, context=None):
        """Build system prompt with policies for specific intent"""
        
        intent = self.get_intent_details(intent_code)
        policies = self.knowledge_base.search(intent["name"])
        
        policy_context = "\n".join([f"{k.upper()}:\n{v}" for k, v in policies])
        
        system_prompt = f"""You are a professional customer service AI for a quick-commerce platform.

INTENT: {intent['name']}

RELEVANT POLICIES:
{policy_context}

RULES:
1. NEVER invent order status or tracking information
2. NEVER invent tax percentages or customs rules
3. If information is unavailable in our system, explicitly say "I don't have this information"
4. Be professional, concise, and empathetic
5. When denying a request, cite the specific policy
6. Escalate to human support when required
7. Always prioritize retrieved policy data over your general knowledge
8. Ask clarifying questions before providing solutions

TONE: Professional, helpful, empathetic, concise
"""
        
        if context:
            system_prompt += f"\n\nCONTEXT:\n{context}\n"
        
        return system_prompt

    def all_intents(self):
        """Return all available intents for UI"""
        return [
            (code, data["name"], data["icon"]) 
            for code, data in self.intents.items()
        ]
