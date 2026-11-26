import requests

from tests.client import Client
from tests.config import *
from tests.data import make_address, make_item


def test_invalid_uuid():
    client = Client()
    order_id = "invalid-uuid"
    cases = (
        (client.get_order, (), ORDER_PATH),
        (client.change_status, ("PAID",), ORDER_STATUS_PATH),
        (client.cancel_order, ("Nah I'll pass",), ORDER_PATH),
        (client.remove_order, ("Nah I'll pass",), REMOVE_ORDER_PATH),
        (client.receive_payment, (), PAYMENT_RECEIVED_PATH),
        (client.start_cooking, (), START_COOKING_PATH),
        (client.assign_courier, (), ASSIGN_COURIER_PATH),
        (client.deliver_order, (), DELIVER_ORDER_PATH),
        (client.get_order_board, (), ORDER_BOARD_PATH),
    )

    for method, args, route in cases:
        status, error = method(order_id, *args)

        assert status == 400, method.__name__
        assert_api_error(error, 400, "Bad Request", f"/{route.format(order_id=order_id)}")


def test_not_found():
    client = Client()
    order_id = MISSING_ORDER_ID
    cases = (
        (client.get_order, (), ORDER_PATH),
        (client.change_status, ("PAID",), ORDER_STATUS_PATH),
        (client.cancel_order, ("Nah I'll pass",), ORDER_PATH),
        (client.remove_order, ("Nah I'll pass",), REMOVE_ORDER_PATH),
        (client.receive_payment, (), PAYMENT_RECEIVED_PATH),
        (client.start_cooking, (), START_COOKING_PATH),
        (client.assign_courier, (), ASSIGN_COURIER_PATH),
        (client.deliver_order, (), DELIVER_ORDER_PATH),
        (client.get_order_board, (), ORDER_BOARD_PATH),
    )

    for method, args, route in cases:
        status, error = method(order_id, *args)

        assert status == 404, method.__name__
        assert_api_error(error, 404, "Not Found", f"/{route.format(order_id=order_id)}")


def test_create_order_invalid_data():
    client = Client()
    address_without_city = make_address()
    address_without_city.city = ""
    item_with_unknown_size = make_item()
    item_with_unknown_size.size = "GIGA_LARGE"
    cases = (
        (make_address(), []),
        (make_address(), [make_item(qty=0)]),
        (make_address(), [item_with_unknown_size]),
        (address_without_city, [make_item()]),
    )

    for method, route in ((client.create_order, ORDERS_PATH), (client.create_workflow_order, WORKFLOW_PATH)):
        for address, items in cases:
            status, error = method(address, items)

            assert status == 400, method.__name__
            assert_api_error(error, 400, "Bad Request", f"/{route}")


def test_change_status_invalid_status():
    client = Client()
    created_status, order = client.create_order(make_address(), [make_item()])
    assert created_status == 201

    status, error = client.change_status(order.id, "MELTING")

    assert status == 400
    assert_api_error(error, 400, "Bad Request", f"/{ORDER_STATUS_PATH.format(order_id=order.id)}")


def test_delete_routes_invalid_reason():
    client = Client()
    created_status, order = client.create_order(make_address(), [make_item()])
    assert created_status == 201

    for method, route in ((client.cancel_order, ORDER_PATH), (client.remove_order, REMOVE_ORDER_PATH)):
        path = f"/{route.format(order_id=order.id)}"
        response = requests.delete(f"{API_ADDRESS}{path}")

        assert response.status_code == 400, method.__name__
        assert_api_error(response.json(), 400, "Bad Request", path)
        for reason in (" ", "a" * 1001):
            status, error = method(order.id, reason)

            assert status == 400, method.__name__
            assert_api_error(error, 400, "Bad Request", path)


def test_forbidden_transition():
    client = Client()
    created_status, created_order = client.create_order(make_address(), [make_item()])
    assert created_status == 201
    order_id = created_order.id

    forbidden_transitions = [
        ("CREATED", "DELIVERED"),
        ("PAID", "CREATED"),
        ("DELIVERED", "OUT_FOR_DELIVERY"),
    ]
    status_chain = ["CREATED", "PAID", "COOKING", "OUT_FOR_DELIVERY", "DELIVERED"]
    current_status = created_order.status
    for source_status, target_status in forbidden_transitions:
        start = status_chain.index(current_status) + 1
        end = status_chain.index(source_status) + 1
        for next_status in status_chain[start:end]:
            status, order = client.change_status(order_id, next_status)
            assert status == 200
            assert order.status == next_status
            current_status = order.status

        status, error = client.change_status(order_id, target_status)

        assert status == 409, f"{source_status} -> {target_status}"
        assert_api_error(error, 409, "Conflict", f"/{ORDER_STATUS_PATH.format(order_id=order_id)}")


def test_different_cancel_reason():
    client = Client()
    created_status, order = client.create_order(make_address(), [make_item()])
    assert created_status == 201
    cancelled_status, _ = client.cancel_order(order.id, "Reason 1")
    assert cancelled_status == 204

    for method, route in ((client.cancel_order, ORDER_PATH), (client.remove_order, REMOVE_ORDER_PATH)):
        status, error = method(order.id, "Reason 2")

        assert status == 409, method.__name__
        assert_api_error(error, 409, "Conflict", f"/{route.format(order_id=order.id)}")


def test_workflow_rejects_cancelled_order():
    client = Client()
    created_status, order = client.create_order(make_address(), [make_item()])
    assert created_status == 201
    cancelled_status, _ = client.cancel_order(order.id, "Nah I'll pass")
    assert cancelled_status == 204
    cases = (
        (client.receive_payment, PAYMENT_RECEIVED_PATH),
        (client.start_cooking, START_COOKING_PATH),
        (client.assign_courier, ASSIGN_COURIER_PATH),
        (client.deliver_order, DELIVER_ORDER_PATH),
    )

    for method, route in cases:
        status, error = method(order.id)

        assert status == 500, method.__name__
        assert_api_error(error, 500, "Internal Server Error", f"/{route.format(order_id=order.id)}")


def test_workflow_rejects_skipped_steps():
    client = Client()
    status, order = client.create_workflow_order(make_address(), [make_item()])
    assert status == 200
    order_id = order.order_id

    status, error = client.start_cooking(order_id)
    assert status == 500
    assert_api_error(
        error, 500, "Internal Server Error", f"/{START_COOKING_PATH.format(order_id=order_id)}",
    )

    status, order = client.receive_payment(order_id)
    assert status == 200
    assert order.current_status == "PAID"

    status, error = client.assign_courier(order_id)
    assert status == 500
    assert_api_error(
        error, 500, "Internal Server Error", f"/{ASSIGN_COURIER_PATH.format(order_id=order_id)}",
    )

    status, order = client.start_cooking(order_id)
    assert status == 200
    assert order.current_status == "COOKING"

    status, error = client.deliver_order(order_id)
    assert status == 500
    assert_api_error(
        error, 500, "Internal Server Error", f"/{DELIVER_ORDER_PATH.format(order_id=order_id)}",
    )

    status, board = client.get_order_board(order_id)
    assert status == 200
    assert board.current_status == "COOKING"


def assert_api_error(error, status, reason, path):
    assert error["status"] == status
    assert error["error"] == reason
    assert error["path"] == path
