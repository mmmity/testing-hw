from typing import List

from tests.types import Address, OrderItem


PRICE_BY_SIZE = {"SMALL": 8.0, "MEDIUM": 10.0, "LARGE": 12.0}


def make_address(postcode: str = "14898") -> Address:
    return Address(
        city="Brunei",
        street="Bruneeva",
        house="993",
        apartment="68",
        postcode=postcode,
    )


def make_item(qty: int = 2) -> OrderItem:
    return OrderItem(name="Pizza Mozzarella, rella rella", size="MEDIUM", qty=qty)


def calculate_total(items: List[OrderItem]) -> float:
    return sum(PRICE_BY_SIZE[item.size] * item.qty for item in items)
