"""
Knowledge base for RAG - stores policies and documentation
"""

KNOWLEDGE_BASE = {
    "return_policy": """
RETURN POLICY:
- Non-perishable items: Returnable within 30 days if unopened
- Perishable items: NOT returnable after delivery (frozen, fresh produce, dairy, meat)
- Damaged items: Eligible for replacement or refund within 7 days
- Missing items: Eligible for refund or replacement within 30 days
- Opened products: May not be eligible for return (must be in original condition)
- Restocking fee: Not applicable for defective items, applies to non-defective returns
""",

    "shipping_policy": """
SHIPPING POLICY:
- Domestic (USA): 2 days standard, 1 day express
- International: 5-12 days depending on destination
- Customs may cause delays (1-5 days)
- Tracking available for all orders via tracking number
- Hazardous items restricted in certain countries
- Perishable items available for express delivery only
- Free shipping on orders over $50 (domestic only)
""",

    "perishable_items": """
PERISHABLE ITEMS:
- Frozen products (ice cream, frozen vegetables, frozen meat)
- Fresh produce (vegetables, fruits, berries)
- Dairy products (milk, cheese, yogurt)
- Meat and seafood (fresh, chilled)
- Baked goods (cakes, pastries - if fresh)
- Cannot be returned after delivery
- Require express shipping for quality
- Temperature-controlled handling mandatory
""",

    "tax_and_customs": """
TAX AND CUSTOMS INFORMATION:
- USA: Tax varies by state, no customs for domestic
- UK: 20% VAT applies, post-Brexit customs rules apply
- Germany: 19% VAT, EU regulations
- Japan: 10% tax, strict food import restrictions
- Australia: 10% GST, strict biosecurity on fresh items
- Import duties apply to international orders
- We cannot predict exact tax - depends on destination
- Declared value used for customs calculation
""",

    "international_shipping": """
INTERNATIONAL SHIPPING:
- Destination verification required
- Customs forms prepared by us
- Hazardous items may be restricted
- Fresh/perishable items heavily restricted to certain countries
- Delivery times: 5-12 days (after customs clearance)
- Insurance available for orders over $200
- Restrictions: Check country-specific regulations
- Some items cannot be shipped internationally
""",

    "order_status": """
ORDER STATUS DEFINITIONS:
- Processing: Order received, being prepared
- Out for Delivery: In transit to your address
- Delivered: Successfully delivered to address
- Cancelled: Order cancelled by customer
- Delayed: Experiencing shipping delays
Each status comes with estimated or actual delivery date
""",

    "damaged_items": """
DAMAGED ITEM POLICY:
- Report within 7 days of delivery
- Provide photos and description
- Eligible for replacement or full refund
- We arrange return shipping at no cost
- Processing time: 3-5 business days
- Escalate to human agent if item value > $500
""",

    "missing_items": """
MISSING ITEM POLICY:
- Report within 30 days of delivery
- Provide order ID and item description
- Eligible for refund or replacement
- We investigate carrier records
- Processing time: 5-7 business days
- Common causes: Carrier error, address issues
""",

    "cancellation_policy": """
CANCELLATION POLICY:
- Can cancel only if order still "processing"
- Cannot cancel orders already shipped
- Refund issued within 5-7 business days
- Processing fee may apply (contact support)
- No refund for orders marked delivered
""",

    "payment_issues": """
PAYMENT ISSUE RESOLUTION:
- We do not store payment details
- Contact payment processor directly (card issuer, PayPal, etc)
- We can verify order was received and payment confirmed
- If charged twice, escalate to human agent
- Refund takes 5-10 business days from processor
- We cannot cancel payment - only refund at our end
""",

    "escalation": """
ESCALATION CRITERIA:
- Order value > $500
- Payment fraud suspected
- Legal/dispute claims
- Multiple failed resolutions
- Customer safety concerns
- International disputes
- All escalations routed to human agents
"""
}

class KnowledgeBase:
    def __init__(self):
        self.kb = KNOWLEDGE_BASE

    def search(self, query):
        """Search knowledge base for relevant policies"""
        query_lower = query.lower()
        results = []
        
        keywords = {
            "return": ["return_policy", "perishable_items", "damaged_items", "missing_items"],
            "shipping": ["shipping_policy", "international_shipping"],
            "tax": ["tax_and_customs"],
            "customs": ["tax_and_customs", "international_shipping"],
            "perishable": ["perishable_items", "return_policy"],
            "damaged": ["damaged_items", "return_policy"],
            "missing": ["missing_items"],
            "order": ["order_status"],
            "status": ["order_status"],
            "delivery": ["shipping_policy", "order_status"],
            "cancel": ["cancellation_policy"],
            "payment": ["payment_issues"],
            "international": ["international_shipping", "tax_and_customs"],
        }
        
        for keyword, keys in keywords.items():
            if keyword in query_lower:
                for key in keys:
                    if key not in [r[0] for r in results]:
                        results.append((key, self.kb.get(key, "")))
        
        # If no keyword match, return general policies
        if not results:
            results.append(("return_policy", self.kb["return_policy"]))
            results.append(("shipping_policy", self.kb["shipping_policy"]))
        
        return results

    def get_policy(self, policy_name):
        """Get specific policy by name"""
        return self.kb.get(policy_name, "Policy not found")

    def get_all_context(self):
        """Get all policies for context (for RAG)"""
        return "\n\n".join([f"{k.upper()}:\n{v}" for k, v in self.kb.items()])
