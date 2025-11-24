import requests
import json

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/discover"

payload = json.dumps({
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "domain": "beckn.one:DEG:compute-energy:1.0",
    "timestamp": "2025-11-24T11:24:08.317Z",
    "message_id": "87ecca65-9ca6-41f5-b264-e4eb37c702ed",
    "transaction_id": "7d5ae850-c8da-468c-af58-4d42f67ccf57",
    "bap_id": "ev-charging.sandbox1.com",
    "bap_uri": "https://ev-charging.sandbox1.com.com/bap",
    "ttl": "PT30S",
    "schema_context": [
      "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld"
    ]
  },
  "message": {
    "text_search": "Grid flexibility windows",
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.beckn:gridParameters.renewableMix >= 30)]"
    }
  }
})

headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)