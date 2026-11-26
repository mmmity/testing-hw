from tests.client import Client
from tests.data import calculate_total, make_address, make_item
from tests.types import OrderWorkflowBoard, ShortOrder


def test_create_order():
    client = Client()
    address = make_address()
    items = [make_item()]

    status, order = client.create_order(address, items)

    assert status == 201
    assert order.id
    assert order.address == address
    assert order.items == items
    assert order.status == "CREATED"
    assert order.total_amount == calculate_total(items)
    assert order.currency == "EUR"
    assert order.delivery_zone == "OUTSKIRTS"
    assert order.cancellation_reason is None


def test_delivery_zone():
    client = Client()
    addresses_and_zones = [
        (make_address(postcode="10115"), "CENTER"),
        (make_address(postcode="11000"), "CENTER"),
        (make_address(postcode="14898"), "OUTSKIRTS"),
    ]
    for address, expected_zone in addresses_and_zones:
        status, order = client.create_order(address, [make_item()])

        assert status == 201
        assert order.delivery_zone == expected_zone, address.postcode


def test_get_orders():
    client = Client()
    items = [make_item()]
    created_status, created_order = client.create_order(make_address(), items)
    assert created_status == 201

    status, orders = client.get_orders()

    assert status == 200
    assert isinstance(orders, list)
    assert all(isinstance(order, ShortOrder) for order in orders)
    assert ShortOrder(
        id=created_order.id,
        status="CREATED",
        total_amount=calculate_total(items),
        currency="EUR",
        delivery_zone="OUTSKIRTS",
    ) in orders


def test_cancel_order():
    client = Client()
    created_status, created_order = client.create_order(make_address(), [make_item()])
    assert created_status == 201

    reason = "Nah I'll pass"

    status, body = client.cancel_order(created_order.id, reason)

    assert status == 204
    assert body is None
    status, order = client.get_order(created_order.id)
    assert status == 200
    assert order.status == "CANCELLED"
    assert order.cancellation_reason == reason


def test_remove_order():
    client = Client()
    created_status, created_order = client.create_order(make_address(), [make_item()])
    assert created_status == 201

    status, body = client.remove_order(created_order.id, "Nah I'll pass")

    assert status == 204
    assert body is None
    status, error = client.get_order(created_order.id)
    assert status == 404
    assert error["status"] == 404


def test_workflow():
    client = Client()
    items = [make_item()]

    status, created = client.create_workflow_order(make_address(), items)

    assert status == 200
    order_id = created.order_id
    assert order_id
    assert created.executed_command == "CreateOrder"
    assert created.emitted_event == "OrderCreated"
    assert created.current_status == "CREATED"
    assert created.policy_name == "PaymentRequestedPolicy"
    assert created.suggested_next_command == "ReceivePayment"
    assert created.board == expected_board(order_id, "CREATED", "ReceivePayment", 0, items)

    status, paid = client.receive_payment(order_id)

    assert status == 200
    assert paid.order_id == order_id
    assert paid.executed_command == "ReceivePayment"
    assert paid.emitted_event == "PaymentReceived"
    assert paid.current_status == "PAID"
    assert paid.policy_name == "KitchenStartPolicy"
    assert paid.suggested_next_command == "StartCooking"
    assert paid.board == expected_board(order_id, "PAID", "StartCooking", 1, items)

    status, cooking = client.start_cooking(order_id)

    assert status == 200
    assert cooking.order_id == order_id
    assert cooking.executed_command == "StartCooking"
    assert cooking.emitted_event == "CookingStarted"
    assert cooking.current_status == "COOKING"
    assert cooking.policy_name == "CourierAssignmentPolicy"
    assert cooking.suggested_next_command == "AssignCourier"
    assert cooking.board == expected_board(order_id, "COOKING", "AssignCourier", 2, items)

    status, out_for_delivery = client.assign_courier(order_id)

    assert status == 200
    assert out_for_delivery.order_id == order_id
    assert out_for_delivery.executed_command == "AssignCourier"
    assert out_for_delivery.emitted_event == "CourierAssigned"
    assert out_for_delivery.current_status == "OUT_FOR_DELIVERY"
    assert out_for_delivery.policy_name == "DeliveryCompletionPolicy"
    assert out_for_delivery.suggested_next_command == "DeliverOrder"
    assert out_for_delivery.board == expected_board(order_id, "OUT_FOR_DELIVERY", "DeliverOrder", 3, items)

    status, delivered = client.deliver_order(order_id)

    assert status == 200
    final_board = expected_board(order_id, "DELIVERED", "None", 4, items)
    assert delivered.order_id == order_id
    assert delivered.executed_command == "DeliverOrder"
    assert delivered.emitted_event == "OrderDelivered"
    assert delivered.current_status == "DELIVERED"
    assert delivered.policy_name == "WorkflowCompleted"
    assert delivered.suggested_next_command == "None"
    assert delivered.board == final_board

    status, board = client.get_order_board(order_id)

    assert status == 200
    assert board == final_board


def expected_board(order_id, status, next_command, completed_steps, items):
    return OrderWorkflowBoard(
        id=order_id,
        current_status=status,
        total_amount=calculate_total(items),
        currency="EUR",
        delivery_zone="OUTSKIRTS",
        payment_received=completed_steps >= 1,
        cooking_started=completed_steps >= 2,
        courier_assigned=completed_steps >= 3,
        delivered=completed_steps >= 4,
        next_suggested_command=next_command,
    )
