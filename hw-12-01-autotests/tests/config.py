API_ADDRESS = "http://localhost:8080"
MISSING_ORDER_ID = "77777777-7777-7777-7777-777777777777"

ORDERS_PATH = "orders"
ORDER_PATH = f"{ORDERS_PATH}/{{order_id}}"
ORDER_STATUS_PATH = f"{ORDER_PATH}/status"
REMOVE_ORDER_PATH = f"{ORDER_PATH}/remove"

WORKFLOW_PATH = "seminar/workflow/orders"
PAYMENT_RECEIVED_PATH = f"{WORKFLOW_PATH}/{{order_id}}/payment-received"
START_COOKING_PATH = f"{WORKFLOW_PATH}/{{order_id}}/start-cooking"
ASSIGN_COURIER_PATH = f"{WORKFLOW_PATH}/{{order_id}}/assign-courier"
DELIVER_ORDER_PATH = f"{WORKFLOW_PATH}/{{order_id}}/deliver"
ORDER_BOARD_PATH = f"{WORKFLOW_PATH}/{{order_id}}/board"
