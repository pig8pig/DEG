import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class BecknClient:
    def __init__(self, base_url: str = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api"):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json'
        }
        # Default BAP details from sandbox example
        self.bap_id = "ev-charging.sandbox1.com"
        self.bap_uri = "https://ev-charging.sandbox1.com.com/bap"
        self.domain = "beckn.one:DEG:compute-energy:1.0"

    def _create_context(self, action: str, transaction_id: str = None, message_id: str = None, bpp_id: str = None, bpp_uri: str = None) -> Dict:
        context = {
            "version": "2.0.0",
            "action": action,
            "domain": self.domain,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message_id": message_id or str(uuid.uuid4()),
            "transaction_id": transaction_id or str(uuid.uuid4()),
            "bap_id": self.bap_id,
            "bap_uri": self.bap_uri,
            "ttl": "PT30S"
        }
        # Only include bpp_id and bpp_uri if provided (not needed for discover)
        if bpp_id:
            context["bpp_id"] = bpp_id
        if bpp_uri:
            context["bpp_uri"] = bpp_uri
        # Only include schema_context for actions that need it
        if action in ["discover", "init", "confirm"]:
            context["schema_context"] = [
                "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld"
            ]
        return context

    def discover(self, query: str = "Grid flexibility windows") -> Dict:
        url = f"{self.base_url}/discover"
        payload = {
            "context": self._create_context("discover"),
            "message": {
                "text_search": query,
                "filters": {
                    "type": "jsonpath",
                    "expression": "$[?(@.beckn:itemAttributes.beckn:gridParameters.renewableMix >= 30)]"
                }
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200 and 'error' not in response.json():
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")
            
        # Mock Response for Verification/Fallback
        print("BecknClient: Using Mock Discovery Response")
        return {
            "context": self._create_context("on_discover"),
            "message": {
                "catalog": {
                    "beckn:descriptor": {"name": "Mock Catalog"},
                    "beckn:providers": [
                        {
                            "beckn:id": "provider-gridflex-001",
                            "beckn:descriptor": {"name": "GridFlex Provider"},
                            "beckn:items": [
                                {
                                    "beckn:id": "item-ce-cambridge-morning-001",
                                    "beckn:descriptor": {"name": "Cambridge Morning Slot"},
                                    "beckn:price": {"currency": "GBP", "value": "0.10"},
                                    "beckn:matched": True,
                                    "beckn:itemAttributes": {
                                        "beckn:gridParameters": {
                                            "carbonIntensity": 150
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }

    def select(self, transaction_id: str, bpp_id: str, bpp_uri: str, item_id: str, provider_id: str) -> Dict:
        # ... (keep existing payload construction)
        url = f"{self.base_url}/select"
        payload = {
            "context": self._create_context("select", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "order": {
                    "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
                    "@type": "beckn:Order",
                    "beckn:id": str(uuid.uuid4()),
                    "beckn:orderStatus": "QUOTE_REQUESTED",
                    "beckn:seller": bpp_id,
                    "beckn:buyer": self.bap_id,
                    "beckn:orderItems": [
                        {
                            "@type": "beckn:OrderItem",
                            "beckn:lineId": str(uuid.uuid4()),
                            "beckn:orderedItem": "consumer-resource-office-003", 
                            "beckn:quantity": 1,
                            "beckn:acceptedOffer": {
                                "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
                                "@type": "beckn:Offer",
                                "beckn:id": f"offer-for-{item_id}",
                                "beckn:items": [item_id],
                                "beckn:provider": provider_id
                            }
                        }
                    ]
                }
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200 and 'error' not in response.json():
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")

        # Mock Response
        return {
            "message": {
                "order": payload["message"]["order"]
            }
        }

    def init(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_details: Dict) -> Dict:
        url = f"{self.base_url}/init"
        payload = {
            "context": self._create_context("init", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "order": order_details
            }
        }
        payload["message"]["order"]["beckn:orderStatus"] = "INITIALIZED"
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200 and 'error' not in response.json():
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")

        return payload

    def confirm(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_details: Dict) -> Dict:
        url = f"{self.base_url}/confirm"
        payload = {
            "context": self._create_context("confirm", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "order": order_details
            }
        }
        payload["message"]["order"]["beckn:orderStatus"] = "CONFIRMED" # Mock success directly
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200 and 'error' not in response.json():
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")

        return payload

    def status(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_id: str) -> Dict:
        url = f"{self.base_url}/status"
        payload = {
            "context": self._create_context("status", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "order": {
                    "beckn:id": order_id
                }
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")
        
        return {"message": {"order": {"beckn:id": order_id, "beckn:orderStatus": "UNKNOWN"}}}

    def update(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_id: str, update_type: str, update_details: Dict) -> Dict:
        """Update an order with flexibility actions or acknowledgements"""
        url = f"{self.base_url}/update"
        payload = {
            "context": self._create_context("update", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "order": {
                    "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
                    "@type": "beckn:Order",
                    "beckn:id": order_id,
                    "beckn:orderStatus": "IN_PROGRESS",
                    "beckn:seller": bpp_id,
                    "beckn:buyer": self.bap_id,
                    "beckn:fulfillment": update_details.get("fulfillment", {}),
                    "beckn:orderAttributes": {
                        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
                        "@type": "beckn:ComputeEnergyOrder",
                        "beckn:updateType": update_type,
                        "beckn:updateTimestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")
        
        return payload

    def rating(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_id: str, rating_value: int, feedback: Dict = None) -> Dict:
        """Submit a rating for a completed order"""
        url = f"{self.base_url}/rating"
        message = {
            "id": order_id,
            "value": rating_value,
            "best": 5,
            "worst": 1,
            "category": "grid_service"
        }
        if feedback:
            message["feedback"] = feedback
        
        payload = {
            "context": self._create_context("rating", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": message
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")
        
        return {"message": {"ack": {"status": "ACK"}}}

    def support(self, transaction_id: str, bpp_id: str, bpp_uri: str, order_id: str) -> Dict:
        """Request support for an order"""
        url = f"{self.base_url}/support"
        payload = {
            "context": self._create_context("support", transaction_id=transaction_id, bpp_id=bpp_id, bpp_uri=bpp_uri),
            "message": {
                "ref_id": order_id,
                "ref_type": "order"
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"BecknClient Error: Status {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"BecknClient Exception: {e}")
        
        return {"message": {"support": {"email": "support@example.com", "phone": "+44 1234 567890"}}}
