from typing import Dict, List, Tuple

import requests as req

from tests.config import *
from tests.types import *


class Client:
    def __init__(self, api_address: str = API_ADDRESS):
        self.api_address = api_address

    def get_orders(self) -> Tuple[int, List[ShortOrder] | Dict]:
        response = req.get(
            f"{self.api_address}/{ORDERS_PATH}",
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _orders_from_json(data)

    def create_order(self, address: Address, items: List[OrderItem]) -> Tuple[int, Order | Dict]:
        response = req.post(
            f"{self.api_address}/{ORDERS_PATH}",
            json={"address": vars(address), "items": [vars(item) for item in items]},
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _order_from_json(data)

    def get_order(self, order_id: str) -> Tuple[int, Order | Dict]:
        response = req.get(
            f"{self.api_address}/{ORDER_PATH.format(order_id=order_id)}",
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _order_from_json(data)

    def change_status(self, order_id: str, status: str) -> Tuple[int, Order | Dict]:
        response = req.patch(
            f"{self.api_address}/{ORDER_STATUS_PATH.format(order_id=order_id)}",
            json={"status": status},
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _order_from_json(data)

    def cancel_order(self, order_id: str, reason: str) -> Tuple[int, Dict | None]:
        response = req.delete(
            f"{self.api_address}/{ORDER_PATH.format(order_id=order_id)}",
            params={"reason": reason},
        )
        return response.status_code, response.json() if response.content else None

    def remove_order(self, order_id: str, reason: str) -> Tuple[int, Dict | None]:
        response = req.delete(
            f"{self.api_address}/{REMOVE_ORDER_PATH.format(order_id=order_id)}",
            params={"reason": reason},
        )
        return response.status_code, response.json() if response.content else None

    def create_workflow_order(self, address: Address, items: List[OrderItem]) -> Tuple[int, OrderWorkflow | Dict]:
        response = req.post(
            f"{self.api_address}/{WORKFLOW_PATH}",
            json={"address": vars(address), "items": [vars(item) for item in items]},
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _workflow_from_json(data)

    def receive_payment(self, order_id: str) -> Tuple[int, OrderWorkflow | Dict]:
        return self._workflow_step(order_id, PAYMENT_RECEIVED_PATH)

    def start_cooking(self, order_id: str) -> Tuple[int, OrderWorkflow | Dict]:
        return self._workflow_step(order_id, START_COOKING_PATH)

    def assign_courier(self, order_id: str) -> Tuple[int, OrderWorkflow | Dict]:
        return self._workflow_step(order_id, ASSIGN_COURIER_PATH)

    def deliver_order(self, order_id: str) -> Tuple[int, OrderWorkflow | Dict]:
        return self._workflow_step(order_id, DELIVER_ORDER_PATH)

    def get_order_board(self, order_id: str) -> Tuple[int, OrderWorkflowBoard | Dict]:
        response = req.get(
            f"{self.api_address}/{ORDER_BOARD_PATH.format(order_id=order_id)}",
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _board_from_json(data)

    def _workflow_step(self, order_id: str, path: str) -> Tuple[int, OrderWorkflow | Dict]:
        response = req.post(
            f"{self.api_address}/{path.format(order_id=order_id)}",
        )
        data = response.json()
        if not 200 <= response.status_code < 300:
            return response.status_code, data
        return response.status_code, _workflow_from_json(data)


def _orders_from_json(data: List[Dict]) -> List[ShortOrder]:
    orders = []
    for entry in data:
        order = ShortOrder(
            id=entry["id"],
            status=entry["status"],
            total_amount=float(entry["totalAmount"]),
            currency=entry["currency"],
            delivery_zone=entry["deliveryZone"],
        )
        orders.append(order)
    return orders


def _order_from_json(data: Dict) -> Order:
    address = Address(
        city=data["address"]["city"],
        street=data["address"]["street"],
        house=data["address"]["house"],
        apartment=data["address"].get("apartment"),
        postcode=data["address"]["postcode"],
    )

    items = []
    for entry in data["items"]:
        item = OrderItem(
            name=entry["name"],
            size=entry["size"],
            qty=entry["qty"],
        )
        items.append(item)

    order = Order(
        id=data["id"],
        address=address,
        items=items,
        status=data["status"],
        total_amount=float(data["totalAmount"]),
        currency=data["currency"],
        delivery_zone=data["deliveryZone"],
        cancellation_reason=data["cancellationReason"],
    )
    return order


def _workflow_from_json(data: Dict) -> OrderWorkflow:
    workflow = OrderWorkflow(
        order_id=data["orderId"],
        executed_command=data["executedCommand"],
        emitted_event=data["emittedEvent"],
        current_status=data["currentStatus"],
        policy_name=data["policyName"],
        suggested_next_command=data["suggestedNextCommand"],
        explanation=data["explanation"],
        board=_board_from_json(data["board"]),
    )
    return workflow


def _board_from_json(data: Dict) -> OrderWorkflowBoard:
    board = OrderWorkflowBoard(
        id=data["id"],
        current_status=data["currentStatus"],
        total_amount=float(data["totalAmount"]),
        currency=data["currency"],
        delivery_zone=data["deliveryZone"],
        payment_received=data["paymentReceived"],
        cooking_started=data["cookingStarted"],
        courier_assigned=data["courierAssigned"],
        delivered=data["delivered"],
        next_suggested_command=data["nextSuggestedCommand"],
    )
    return board
