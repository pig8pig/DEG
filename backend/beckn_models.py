from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# --- A. Grid Source Model ---
class GridSource(BaseModel):
    region_id: str
    time_series_cost: List[tuple]  # List of (timestamp, cost)
    carbon_intensity: Optional[List[tuple]] = None # List of (timestamp, co2)
    availability: bool = True

# --- B. Compute Cluster/Node Model ---
class ComputeNode(BaseModel):
    node_id: str
    cluster_id: str
    region_id: str
    max_power_kw: float
    idle_power_kw: float
    compute_capacity: Dict[str, Any] # e.g. {'cpu_cores': 64, ...}
    variable_cost_per_hr: float
    
    # Dynamic state
    current_power_draw_kw: float = 0.0
    is_available: bool = True

# --- C. Compute Job Model ---
class ComputeJob(BaseModel):
    job_id: str
    num_computations: float # FLOPs or core-hours
    estimated_runtime_hrs: float
    gpu_cluster_preference: Optional[List[str]] = None
    grid_source_preference: Optional[List[str]] = None
    start_time_earliest: Optional[datetime] = None
    deadline_latest: Optional[datetime] = None
    power_profile: Optional[Dict[str, Any]] = None # Simplified as dict for now
    priority: int = 1
    
    # Status
    status: str = "PENDING" # PENDING, ASSIGNED, COMPLETED, FAILED

# --- Beckn Protocol Models ---

class BecknContext(BaseModel):
    version: str = "2.0.0"
    action: str
    domain: str = "beckn.one:DEG:compute-energy:1.0"
    timestamp: datetime
    message_id: str
    transaction_id: str
    bap_id: str
    bap_uri: str
    bpp_id: Optional[str] = None
    bpp_uri: Optional[str] = None
    ttl: str = "PT30S"

class BecknDescriptor(BaseModel):
    name: str = Field(..., alias="schema:name")
    short_desc: Optional[str] = Field(None, alias="beckn:shortDesc")
    long_desc: Optional[str] = Field(None, alias="beckn:longDesc")
    images: Optional[List[str]] = Field(None, alias="schema:image")

    class Config:
        populate_by_name = True

class BecknPrice(BaseModel):
    currency: str
    value: str = Field(..., alias="price") # In the example it is "price" not "value" inside beckn:price object? 
    # Wait, example says: "beckn:price": { "currency": "GBP", "price": 0.102 }
    # So the field name in the JSON is 'price', mapping to our 'value' field.

    class Config:
        populate_by_name = True

class BecknGridParameters(BaseModel):
    grid_area: str = Field(..., alias="gridArea")
    grid_zone: str = Field(..., alias="gridZone")
    renewable_mix: float = Field(..., alias="renewableMix")
    renewable_mix_unit: str = Field("percent", alias="renewableMixUnit")
    carbon_intensity: float = Field(..., alias="carbonIntensity")
    carbon_intensity_unit: str = Field("gCO2/kWh", alias="carbonIntensityUnit")

    class Config:
        populate_by_name = True

class BecknTimeWindow(BaseModel):
    start: datetime
    end: datetime
    duration: Optional[str] = None

class BecknComputeEnergyWindow(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/ComputeEnergy/v1/context.jsonld", alias="@context")
    type: str = Field("beckn:ComputeEnergyWindow", alias="@type")
    slot_id: str = Field(..., alias="beckn:slotId")
    grid_parameters: BecknGridParameters = Field(..., alias="beckn:gridParameters")
    time_window: BecknTimeWindow = Field(..., alias="beckn:timeWindow")
    # pricing and capacity parameters could be added here

    class Config:
        populate_by_name = True

class BecknItem(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld", alias="@context")
    type: str = Field("beckn:Item", alias="@type")
    id: str = Field(..., alias="beckn:id")
    descriptor: BecknDescriptor = Field(..., alias="beckn:descriptor")
    price: Optional[BecknPrice] = Field(None, alias="beckn:price")
    item_attributes: Optional[BecknComputeEnergyWindow] = Field(None, alias="beckn:itemAttributes")
    matched: bool = False # Internal use

    class Config:
        populate_by_name = True

class BecknProvider(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld", alias="@context")
    type: str = Field("beckn:Provider", alias="@type")
    id: str = Field(..., alias="beckn:id")
    descriptor: BecknDescriptor = Field(..., alias="beckn:descriptor")
    items: List[BecknItem] = Field(..., alias="beckn:items")

    class Config:
        populate_by_name = True

class BecknCatalog(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld", alias="@context")
    type: str = Field("beckn:Catalog", alias="@type")
    descriptor: BecknDescriptor = Field(..., alias="beckn:descriptor")
    providers: List[BecknProvider] = Field(..., alias="beckn:providers")

    class Config:
        populate_by_name = True

class BecknOffer(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld", alias="@context")
    type: str = Field("beckn:Offer", alias="@type")
    id: str = Field(..., alias="beckn:id")
    descriptor: BecknDescriptor = Field(..., alias="beckn:descriptor")
    provider_id: str = Field(..., alias="beckn:provider")
    item_ids: List[str] = Field(..., alias="beckn:items")
    price: BecknPrice = Field(..., alias="beckn:price")

    class Config:
        populate_by_name = True

class BecknOrderItem(BaseModel):
    type: str = Field("beckn:OrderItem", alias="@type")
    line_id: str = Field(..., alias="beckn:lineId")
    ordered_item_id: str = Field(..., alias="beckn:orderedItem")
    quantity: int = Field(1, alias="beckn:quantity")
    accepted_offer: BecknOffer = Field(..., alias="beckn:acceptedOffer")
    item_attributes: Optional[BecknComputeEnergyWindow] = Field(None, alias="beckn:orderItemAttributes")

    class Config:
        populate_by_name = True

class OrderState(str, Enum):
    CREATED = "Created"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In-Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    # Beckn states
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    INITIALIZED = "INITIALIZED"
    CONFIRMED = "CONFIRMED"

class BecknOrder(BaseModel):
    context: str = Field("https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/draft/schema/core/v2/context.jsonld", alias="@context")
    type: str = Field("beckn:Order", alias="@type")
    id: str = Field(..., alias="beckn:id")
    state: str = Field(..., alias="beckn:orderStatus")
    seller_id: str = Field(..., alias="beckn:seller")
    buyer_id: str = Field(..., alias="beckn:buyer")
    items: List[BecknOrderItem] = Field(..., alias="beckn:orderItems")
    
    # Internal link
    job_details: Optional[ComputeJob] = None

    class Config:
        populate_by_name = True

class BecknMessage(BaseModel):
    catalog: Optional[BecknCatalog] = None
    order: Optional[BecknOrder] = None

class BecknRequest(BaseModel):
    context: BecknContext
    message: BecknMessage
