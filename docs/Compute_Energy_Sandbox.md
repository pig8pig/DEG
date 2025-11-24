# POST Discover

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

# POST Select

import requests

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/select"

payload = "{\n  \"context\": {\n    \"version\": \"2.0.0\",\n    \"action\": \"select\",\n    \"domain\": \"beckn.one:DEG:compute-energy:1.0\",\n    \"timestamp\": \"2025-11-24T11:24:08.317Z\",\n    \"message_id\": \"c4dc4355-855e-4a0c-a1f8-869a823543fe\",\n    \"transaction_id\": \"a2967a84-48b7-4733-a841-f5d6eb98729b\",\n    \"bap_id\": \"ev-charging.sandbox1.com\",\n    \"bap_uri\": \"https://ev-charging.sandbox1.com.com/bap\",\n    \"bpp_id\": \"ev-charging.sandbox1.com\",\n    \"bpp_uri\": \"https://ev-charging.sandbox1.com.com/bpp\",\n    \"ttl\": \"PT30S\",\n    \"schema_context\": [\n      \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\"\n    ]\n  },\n  \"message\": {\n    \"order\": {\n      \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n      \"@type\": \"beckn:Order\",\n      \"beckn:id\": \"<your-beckn-unqiuely-created-order-id>\",\n      \"beckn:orderStatus\": \"QUOTE_REQUESTED\",\n      \"beckn:seller\": \"ev-charging.sandbox1.com\",\n      \"beckn:buyer\": \"ev-charging.sandbox1.com\",\n      \"beckn:orderItems\": [\n        {\n          \"@type\": \"beckn:OrderItem\",\n          \"beckn:lineId\": \"order-item-ce-001\",\n          \"beckn:orderedItem\": \"consumer-resource-office-003\",\n          \"beckn:quantity\": 1,\n          \"beckn:acceptedOffer\": {\n            \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n            \"@type\": \"beckn:Offer\",\n            \"beckn:id\": \"offer-ce-cambridge-morning-001\",\n            \"beckn:descriptor\": {\n              \"@type\": \"beckn:Descriptor\",\n              \"schema:name\": \"Cambridge-East Morning Window\"\n            },\n            \"beckn:items\": [\n              \"item-ce-cambridge-morning-001\"\n            ],\n            \"beckn:provider\": \"gridflex-agent-uk\",\n            \"beckn:price\": {\n              \"currency\": \"GBP\",\n              \"price\": 0.102\n            },\n            \"beckn:offerAttributes\": {\n              \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\",\n              \"@type\": \"beckn:ComputeEnergyPricing\",\n              \"beckn:unit\": \"per_kWh\",\n              \"beckn:priceStability\": \"stable\"\n            }\n          }\n        }\n      ]\n    }\n  }\n}\n"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Init

import requests
import json

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/init"

payload = json.dumps({
  "context": {
    "version": "2.0.0",
    "action": "init",
    "domain": "beckn.one:DEG:compute-energy:1.0",
    "timestamp": "2025-11-24T11:24:08.317Z",
    "message_id": "6da4ede5-223e-4c09-802b-b49c986f41b5",
    "transaction_id": "ab2d7340-f470-47c9-8d20-a19f0e6e47f9",
    "bap_id": "ev-charging.sandbox1.com",
    "bap_uri": "https://ev-charging.sandbox1.com.com/bap",
    "bpp_id": "ev-charging.sandbox1.com",
    "bpp_uri": "https://ev-charging.sandbox1.com.com/bpp",
    "ttl": "PT30S",
    "schema_context": [
      "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld"
    ]
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "<your-beckn-order-id>",
      "beckn:orderStatus": "INITIALIZED",
      "beckn:seller": "provider-gridflex-001",
      "beckn:buyer": "buyer-compflex-001",
      "beckn:invoice": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "schema:Invoice",
        "schema:customer": {
          "email": "leena.jones@computecloud.ai",
          "phone": "+44 7911 123456",
          "legalName": "ComputeCloud.ai",
          "address": {
            "streetAddress": "123 Main St",
            "addressLocality": "Cambridge",
            "addressRegion": "East England",
            "postalCode": "CB1 2AB",
            "addressCountry": "GB"
          }
        }
      },
      "beckn:orderItems": [
        {
          "@type": "beckn:OrderItem",
          "beckn:lineId": "order-item-ce-001",
          "beckn:orderedItem": "consumer-resource-office-003",
          "beckn:quantity": 1,
          "beckn:acceptedOffer": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:id": "offer-ce-cambridge-morning-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Cambridge Morning Compute Slot"
            },
            "beckn:provider": "provider-gridflex-001",
            "beckn:items": [
              "item-ce-cambridge-morning-001"
            ],
            "beckn:price": {
              "currency": "GBP",
              "price": 0.102
            },
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
              "@type": "beckn:ComputeEnergyPricing",
              "beckn:unit": "per_kWh",
              "beckn:priceStability": "stable"
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-ce-cambridge-001",
        "beckn:mode": "GRID-BASED",
        "beckn:status": "PENDING",
        "beckn:deliveryAttributes": {
          "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
          "@type": "beckn:ComputeEnergyFulfillment",
          "beckn:computeLoad": 1.2,
          "beckn:computeLoadUnit": "MW",
          "beckn:location": {
            "@type": "beckn:Location",
            "geo": {
              "type": "Point",
              "coordinates": [
                0.1218,
                52.2053
              ]
            },
            "address": {
              "streetAddress": "ComputeCloud Data Centre",
              "addressLocality": "Cambridge",
              "addressRegion": "East England",
              "postalCode": "CB1 2AB",
              "addressCountry": "GB"
            }
          },
          "beckn:timeWindow": {
            "start": "2025-11-17T10:00:00Z",
            "end": "2025-11-17T14:00:00Z"
          },
          "beckn:workloadMetadata": {
            "workloadType": "AI_TRAINING",
            "workloadId": "batch-a-001",
            "gpuHours": 4800,
            "carbonBudget": 576,
            "carbonBudgetUnit": "kgCO2"
          }
        }
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
        "@type": "beckn:ComputeEnergyOrder",
        "beckn:requestType": "compute_slot_reservation",
        "beckn:priority": "medium",
        "beckn:flexibilityLevel": "high"
      }
    }
  }
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Confirm

import requests
import json

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/confirm"

payload = json.dumps({
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "domain": "beckn.one:DEG:compute-energy:1.0",
    "timestamp": "2025-11-24T11:24:08.317Z",
    "message_id": "ae8dc42e-6707-4c8c-a416-db5dd8493f6d",
    "transaction_id": "5a79f50a-1cb1-4c68-bea0-ddab4f0f66b3",
    "bap_id": "ev-charging.sandbox1.com",
    "bap_uri": "https://ev-charging.sandbox1.com.com/bap",
    "bpp_id": "ev-charging.sandbox1.com",
    "bpp_uri": "https://ev-charging.sandbox1.com.com/bpp",
    "ttl": "PT30S",
    "schema_context": [
      "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld"
    ]
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "<your-beckn-order-id>",
      "beckn:orderStatus": "PENDING",
      "beckn:seller": "gridflex-agent-uk",
      "beckn:buyer": "compflex-buyer-001",
      "beckn:invoice": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "schema:Invoice",
        "schema:customer": {
          "email": "leena.jones@computecloud.ai",
          "phone": "+44 7911 123456",
          "legalName": "ComputeCloud.ai",
          "address": {
            "streetAddress": "123 Main St",
            "addressLocality": "Cambridge",
            "addressRegion": "East England",
            "postalCode": "CB1 2AB",
            "addressCountry": "GB"
          }
        }
      },
      "beckn:orderItems": [
        {
          "@type": "beckn:OrderItem",
          "beckn:lineId": "order-item-ce-001",
          "beckn:orderedItem": "item-ce-manchester-afternoon-001",
          "beckn:quantity": 1,
          "beckn:acceptedOffer": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:id": "offer-ce-cambridge-morning-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Cambridge Morning Compute Slot"
            },
            "beckn:provider": "provider-gridflex-001",
            "beckn:items": [
              "item-ce-cambridge-morning-001"
            ],
            "beckn:price": {
              "currency": "GBP",
              "price": 0.102
            },
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
              "@type": "beckn:ComputeEnergyPricing",
              "beckn:unit": "per_kWh",
              "beckn:priceStability": "stable"
            }
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
            "@type": "beckn:ComputeEnergyWindow",
            "beckn:slotId": "slot-cambridge-morning-20251117-001",
            "beckn:gridParameters": {
              "gridArea": "Cambridge-East",
              "gridZone": "UK-EAST-1",
              "renewableMix": 80,
              "carbonIntensity": 120,
              "carbonIntensityUnit": "gCO2/kWh",
              "frequency": 50,
              "frequencyUnit": "Hz"
            },
            "beckn:timeWindow": {
              "start": "2025-11-17T10:00:00Z",
              "end": "2025-11-17T14:00:00Z",
              "duration": "PT4H"
            },
            "beckn:capacityParameters": {
              "availableCapacity": 3.8,
              "capacityUnit": "MW",
              "reservedCapacity": 1.2
            },
            "beckn:pricingParameters": {
              "currency": "GBP",
              "unit": "per_kWh",
              "spotPrice": 0.102,
              "priceStability": "stable",
              "estimatedCost": 489.6
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-ce-cambridge-001",
        "beckn:mode": "GRID-BASED",
        "beckn:status": "CONFIRMED",
        "beckn:deliveryAttributes": {
          "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
          "@type": "beckn:ComputeEnergyFulfillment",
          "beckn:computeLoad": 1.2,
          "beckn:computeLoadUnit": "MW",
          "beckn:location": {
            "@type": "beckn:Location",
            "geo": {
              "type": "Point",
              "coordinates": [
                0.1218,
                52.2053
              ]
            },
            "address": {
              "streetAddress": "ComputeCloud Data Centre",
              "addressLocality": "Cambridge",
              "addressRegion": "East England",
              "postalCode": "CB1 2AB",
              "addressCountry": "GB"
            }
          },
          "beckn:timeWindow": {
            "start": "2025-11-17T10:00:00Z",
            "end": "2025-11-17T14:00:00Z"
          },
          "beckn:workloadMetadata": {
            "workloadType": "AI_TRAINING",
            "workloadId": "batch-a-001",
            "gpuHours": 4800,
            "carbonBudget": 576,
            "carbonBudgetUnit": "kgCO2"
          },
          "beckn:confirmationTimestamp": "2025-11-21T15:38:00Z"
        }
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
        "@type": "beckn:ComputeEnergyOrder",
        "beckn:requestType": "compute_slot_reservation",
        "beckn:priority": "medium",
        "beckn:flexibilityLevel": "high",
        "beckn:confirmationTimestamp": "2025-11-21T15:38:00Z"
      },
      "beckn:payment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld",
        "@type": "beckn:ComputeEnergyPayment",
        "beckn:settlement": "next-billing-cycle"
      }
    }
  }
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Update - Work load shift

import requests

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/update"

payload = "{\n    \"context\": {\n        \"version\": \"2.0.0\",\n        \"action\": \"update\",\n        \"domain\": \"beckn.one:DEG:compute-energy:1.0\",\n        \"timestamp\": \"2025-11-24T11:24:08.317Z\",\n        \"message_id\": \"8a4524f7-1ea4-4e1f-8905-c3693ba690ef\",\n        \"transaction_id\": \"9e1b4591-fb34-4582-9715-deaf1d7d2bff\",\n        \"bap_id\": \"ev-charging.sandbox1.com\",\n        \"bap_uri\": \"https://ev-charging.sandbox1.com.com/bap\",\n        \"bpp_id\": \"ev-charging.sandbox1.com\",\n        \"bpp_uri\": \"https://ev-charging.sandbox1.com.com/bpp\",\n        \"ttl\": \"PT30S\"\n    },\n    \"message\": {\n        \"order\": {\n            \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n            \"@type\": \"beckn:Order\",\n            \"beckn:id\": \"<your-backn-order-id>\",\n            \"beckn:orderStatus\": \"IN_PROGRESS\",\n            \"beckn:seller\": \"ev-charging.sandbox1.com\",\n            \"beckn:buyer\": \"ev-charging.sandbox1.com\",\n            \"beckn:fulfillment\": {\n                \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n                \"@type\": \"beckn:Fulfillment\",\n                \"beckn:id\": \"fulfillment-ce-cambridge-001\",\n                \"beckn:mode\": \"GRID-BASED\",\n                \"beckn:status\": \"IN_PROGRESS\",\n                \"beckn:deliveryAttributes\": {\n                    \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\",\n                    \"@type\": \"beckn:ComputeEnergyFulfillment\",\n                    \"beckn:flexibilityAction\": {\n                        \"actionType\": \"workload_shift\",\n                        \"actionReason\": \"grid_stress_response\",\n                        \"actionTimestamp\": \"2025-11-17T14:00:30Z\",\n                        \"shiftDetails\": {\n                            \"shiftedLoad\": 0.3,\n                            \"shiftedLoadUnit\": \"MW\",\n                            \"sourceLocation\": \"Cambridge\",\n                            \"targetLocation\": \"Manchester\",\n                            \"targetOrder\": \"order-ce-manchester-afternoon-001\",\n                            \"estimatedShiftTime\": \"PT5M\"\n                        },\n                        \"batterySupportDetails\": {\n                            \"batterySupportActivated\": true,\n                            \"batteryDischarge\": 0.15,\n                            \"batteryDischargeUnit\": \"MW\",\n                            \"batteryDuration\": \"PT10M\"\n                        },\n                        \"loadReductionCommitment\": {\n                            \"loadReduction\": 0.3,\n                            \"reductionUnit\": \"MW\",\n                            \"responseTime\": \"PT2M\"\n                        }\n                    },\n                    \"beckn:workloadMetadata\": {\n                        \"workloadType\": \"AI_TRAINING\",\n                        \"workloadId\": \"batch-a-001\",\n                        \"workloadStatus\": \"migrating\",\n                        \"checkpointCreated\": true,\n                        \"checkpointTimestamp\": \"2025-11-17T14:00:25Z\"\n                    }\n                }\n            },\n            \"beckn:orderAttributes\": {\n                \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\",\n                \"@type\": \"beckn:ComputeEnergyOrder\",\n                \"beckn:updateType\": \"flexibility_response\",\n                \"beckn:responseToEvent\": \"grid-event-cambridge-20251117-001\",\n                \"beckn:updateTimestamp\": \"2025-11-17T14:00:30Z\"\n            }\n        }\n    }\n}"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Update - Carbon intensity

import requests

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/update"

payload = "{\n    \"context\": {\n        \"version\": \"2.0.0\",\n        \"action\": \"update\",\n        \"domain\": \"beckn.one:DEG:compute-energy:1.0\",\n        \"timestamp\": \"2025-11-24T11:24:08.317Z\",\n        \"message_id\": \"11c55ea5-d551-45c1-9603-5046688c7fac\",\n        \"transaction_id\": \"37e5438f-3cfa-41d6-93b2-89cd5a8d2dbd\",\n        \"bap_id\": \"ev-charging.sandbox1.com\",\n        \"bap_uri\": \"https://ev-charging.sandbox1.com.com/bap\",\n        \"bpp_id\": \"ev-charging.sandbox1.com\",\n        \"bpp_uri\": \"https://ev-charging.sandbox1.com.com/bpp\",\n        \"ttl\": \"PT30S\"\n    },\n    \"message\": {\n        \"order\": {\n            \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n            \"@type\": \"beckn:Order\",\n            \"beckn:id\": \"<your-beckn-order-id>\",\n            \"beckn:orderStatus\": \"IN_PROGRESS\",\n            \"beckn:seller\": \"ev-charging.sandbox1.com\",\n            \"beckn:buyer\": \"ev-charging.sandbox1.com\",\n            \"beckn:fulfillment\": {\n                \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld\",\n                \"@type\": \"beckn:Fulfillment\",\n                \"beckn:id\": \"fulfillment-ce-cambridge-001\",\n                \"beckn:mode\": \"GRID-BASED\",\n                \"beckn:status\": \"IN_PROGRESS\",\n                \"beckn:deliveryAttributes\": {\n                    \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\",\n                    \"@type\": \"beckn:ComputeEnergyFulfillment\",\n                    \"beckn:flexibilityAction\": {\n                        \"actionType\": \"continue_with_acknowledgement\",\n                        \"actionReason\": \"acceptable_carbon_cost_tradeoff\",\n                        \"actionTimestamp\": \"2025-11-17T15:16:15Z\",\n                        \"decision\": {\n                            \"decisionType\": \"continue_execution\",\n                            \"decisionRationale\": \"Carbon intensity spike within acceptable threshold; workload priority justifies increased cost\",\n                            \"acceptedCarbonIntensity\": 320,\n                            \"acceptedCarbonIntensityUnit\": \"gCO2/kWh\",\n                            \"acceptedSpotPrice\": 0.156,\n                            \"acceptedSpotPriceUnit\": \"GBP_per_kWh\",\n                            \"carbonBudgetImpact\": {\n                                \"originalBudget\": 432,\n                                \"projectedEmissions\": 576,\n                                \"budgetExceeded\": 144,\n                                \"budgetExceededUnit\": \"kgCO2\",\n                                \"acceptanceJustification\": \"Critical training deadline; carbon offset planned\"\n                            }\n                        },\n                        \"monitoringParameters\": {\n                            \"alertThreshold\": {\n                                \"maxCarbonIntensity\": 400,\n                                \"maxCarbonIntensityUnit\": \"gCO2/kWh\",\n                                \"maxSpotPrice\": 0.20,\n                                \"maxSpotPriceUnit\": \"GBP_per_kWh\"\n                            },\n                            \"autoShutdownEnabled\": true,\n                            \"autoShutdownThreshold\": {\n                                \"carbonIntensity\": 450,\n                                \"spotPrice\": 0.25\n                            }\n                        }\n                    },\n                    \"beckn:workloadMetadata\": {\n                        \"workloadType\": \"AI_TRAINING\",\n                        \"workloadId\": \"batch-a-001\",\n                        \"workloadStatus\": \"continuing\",\n                        \"workloadPriority\": \"high\",\n                        \"estimatedCompletion\": \"2025-11-17T17:30:00Z\"\n                    }\n                }\n            },\n            \"beckn:orderAttributes\": {\n                \"@context\": \"https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld\",\n                \"@type\": \"beckn:ComputeEnergyOrder\",\n                \"beckn:updateType\": \"alert_acknowledgement\",\n                \"beckn:responseToEvent\": \"grid-event-cambridge-carbon-spike-002\",\n                \"beckn:updateTimestamp\": \"2025-11-17T15:16:15Z\"\n            }\n        }\n    }\n}"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Status

import requests

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/status"

payload = "{\n    \"context\": {\n        \"version\": \"2.0.0\",\n        \"action\": \"status\",\n        \"domain\": \"beckn.one:DEG:compute-energy:1.0\",\n        \"timestamp\": \"2025-11-24T11:24:08.317Z\",\n        \"message_id\": \"040f1bf2-7d73-4240-a22b-b906d8ae7c57\",\n        \"transaction_id\": \"48a4d49e-834a-4790-aa55-d47da0ad077e\",\n        \"bap_id\": \"ev-charging.sandbox1.com\",\n        \"bap_uri\": \"https://ev-charging.sandbox1.com.com/bap\",\n        \"bpp_id\": \"ev-charging.sandbox1.com\",\n        \"bpp_uri\": \"https://ev-charging.sandbox1.com.com/bpp\",\n        \"ttl\": \"PT30S\"\n    },\n    \"message\": {\n        \"order\": {\n            \"beckn:id\": \"<your-beckn-order-id>\"\n        }\n    }\n}"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Rating

import requests
import json

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/rating"

payload = json.dumps({
  "context": {
    "version": "2.0.0",
    "action": "rating",
    "domain": "beckn.one:DEG:compute-energy:1.0",
    "timestamp": "2025-11-24T11:24:08.317Z",
    "message_id": "aa7c1d14-bdf8-4005-be68-a39edd0e7963",
    "transaction_id": "f73648d6-03a8-4926-b22d-b4eb69532b96",
    "bap_id": "ev-charging.sandbox1.com",
    "bap_uri": "https://ev-charging.sandbox1.com.com/bap",
    "bpp_id": "ev-charging.sandbox1.com",
    "bpp_uri": "https://ev-charging.sandbox1.com.com/bpp",
    "ttl": "PT30S"
  },
  "message": {
    "id": "<your-beckn-order-id>",
    "value": 5,
    "best": 5,
    "worst": 1,
    "category": "grid_service",
    "feedback": {
      "comments": "Excellent grid flexibility service! Real-time signals were accurate, workload shifting was seamless, and the carbon savings exceeded expectations. The incentive settlement was transparent and timely.",
      "tags": [
        "accurate-signals",
        "seamless-integration",
        "carbon-savings",
        "transparent-settlement",
        "reliable-service"
      ]
    }
  }
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# POST Support

import requests
import json

url = "https://deg-hackathon-bap-sandbox.becknprotocol.io/api/support"

payload = json.dumps({
  "context": {
    "version": "2.0.0",
    "action": "support",
    "domain": "beckn.one:DEG:compute-energy:1.0",
    "timestamp": "2025-11-24T11:24:08.317Z",
    "message_id": "0be9ca4c-b699-4fe4-a49e-e79718fe84d2",
    "transaction_id": "461bcb75-fabf-405a-9b1a-96315bc681ea",
    "bap_id": "ev-charging.sandbox1.com",
    "bap_uri": "https://ev-charging.sandbox1.com.com/bap",
    "bpp_id": "ev-charging.sandbox1.com",
    "bpp_uri": "https://ev-charging.sandbox1.com.com/bpp",
    "ttl": "PT30S"
  },
  "message": {
    "ref_id": "<your-beckn-order-id>",
    "ref_type": "order"
  }
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)