import json
from datetime import datetime, timedelta

class PolicyEngine:
    def __init__(self, inventory_path="mock_inventory.json"):
        with open(inventory_path, "r") as f:
            self.data = json.load(f)
        self.perishable_items = self.data["perishable_items"]
        self.return_policies = self.data["return_policies"]
        self.countries = self.data["countries"]

    def is_perishable(self, item_name):
        """Check if item is perishable"""
        item_lower = item_name.lower()
        return any(cat in item_lower for cat in self.perishable_items)

    def check_return_eligibility(self, order):
        """Check if order items are returnable"""
        eligibility = {
            "eligible": True,
            "reason": None,
            "options": ["refund"],
            "window_days": 30
        }

        # Check order age
        created = datetime.strptime(order["created_at"], "%Y-%m-%d")
        days_old = (datetime.now() - created).days
        
        if days_old > 30:
            eligibility["eligible"] = False
            eligibility["reason"] = "Return window (30 days) has expired"
            return eligibility

        # Check item conditions
        for item in order["items"]:
            if self.is_perishable(item["name"]):
                eligibility["eligible"] = False
                eligibility["reason"] = "Perishable items cannot be returned after delivery"
                eligibility["options"] = []
                return eligibility
            
            if item["condition"] == "damaged":
                eligibility["options"] = ["replacement", "refund"]
                eligibility["window_days"] = 7
                eligibility["reason"] = "Damaged item - eligible for replacement or refund within 7 days"
                return eligibility

        return eligibility

    def get_tax_info(self, country_name):
        """Get tax and customs info for country"""
        country = self.countries.get(country_name)
        if not country:
            return {
                "available": False,
                "tax_rate": "Unknown - not in system",
                "customs_rules": "Please contact support for this country"
            }
        return {
            "available": True,
            "tax_rate": country["tax_rate"],
            "customs_rules": country["customs_rules"],
            "delivery_days": country["delivery_days"],
            "restricted_items": country["hazardous_restrictions"]
        }

    def check_shipping_restrictions(self, country_name, item_type):
        """Check if item can be shipped to country"""
        country = self.countries.get(country_name)
        if not country:
            return {"restricted": True, "reason": "Country not in system"}
        
        restrictions = country["hazardous_restrictions"]
        if item_type.lower() in restrictions or any(cat in item_type.lower() for cat in restrictions):
            return {
                "restricted": True,
                "reason": f"{item_type} is restricted to {country_name}"
            }
        return {"restricted": False}

    def validate_order_status(self, order):
        """Get order status details"""
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "created_at": order["created_at"],
            "estimated_delivery": order.get("estimated_delivery", "N/A"),
            "delivered_at": order.get("delivered_at", "Not yet delivered"),
            "tracking_number": order.get("tracking_number", "Not available"),
            "items": order["items"],
            "total": order["total"]
        }

    def get_delivery_status_message(self, order):
        """Generate human-readable delivery status"""
        status = order["status"]
        messages = {
            "processing": "Your order is being prepared for shipment.",
            "out_for_delivery": "Your order is out for delivery and should arrive today.",
            "delivered": "Your order has been delivered.",
            "cancelled": "Your order has been cancelled.",
            "delayed": "Your order is delayed. We apologize for the inconvenience."
        }
        return messages.get(status, f"Order status: {status}")

    def can_cancel_order(self, order):
        """Check if order can be cancelled"""
        cancellable_statuses = ["processing"]
        can_cancel = order["status"] in cancellable_statuses
        
        return {
            "can_cancel": can_cancel,
            "reason": "Order cannot be cancelled - already shipped" if not can_cancel else None
        }

    def check_missing_item_policy(self):
        """Get policy for missing items"""
        return {
            "eligible": True,
            "window_days": 30,
            "options": ["refund", "replacement"],
            "process": "Please provide order ID and description. We will investigate and issue replacement or refund."
        }

    def check_damaged_item_policy(self):
        """Get policy for damaged items"""
        return {
            "eligible": True,
            "window_days": 7,
            "options": ["replacement", "refund"],
            "process": "Please provide order ID and photos. We will arrange replacement or refund."
        }

    def get_payment_issue_workflow(self):
        """Workflow for payment issues"""
        return {
            "steps": [
                "Verify payment method used",
                "Check transaction status",
                "Resolve with payment processor if needed",
                "Escalate to human agent if unresolved"
            ],
            "requires_human": True
        }
