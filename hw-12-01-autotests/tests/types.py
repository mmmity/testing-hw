from dataclasses import dataclass
from typing import List

@dataclass
class ShortOrder:
    id: str
    status: str
    total_amount: int
    currency: str
    delivery_zone: str

@dataclass
class Address:
    city: str
    street: str
    house: str
    apartment: str
    postcode: str

@dataclass
class OrderItem:
    name: str
    size: str
    qty: int

@dataclass
class Order:
    id: str
    address: Address
    items: List[OrderItem]
    status: str
    total_amount: int
    currency: str
    delivery_zone: str
    cancellation_reason: str

@dataclass
class OrderWorkflowBoard:
    id: str
    current_status: str
    total_amount: int
    currency: str
    delivery_zone: str
    payment_received: bool
    cooking_started: bool
    courier_assigned: bool
    delivered: bool
    next_suggested_command: str

@dataclass
class OrderWorkflow:
    order_id: str
    executed_command: str
    emitted_event: str
    current_status: str
    policy_name: str
    suggested_next_command: str
    explanation: str
    board: OrderWorkflowBoard