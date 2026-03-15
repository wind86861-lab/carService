from decimal import Decimal
from typing import NamedTuple


class OrderFinancials(NamedTuple):
    profit: Decimal
    master_share: Decimal
    service_share: Decimal


def calculate_order_financials(agreed_price: Decimal, parts_cost: Decimal) -> OrderFinancials:
    """Calculate profit, master share (40%), and service share (60%)."""
    profit = agreed_price - parts_cost
    master_share = (profit * Decimal("0.40")).quantize(Decimal("0.01"))
    service_share = (profit * Decimal("0.60")).quantize(Decimal("0.01"))
    return OrderFinancials(profit=profit, master_share=master_share, service_share=service_share)


def validate_financials(agreed_price: Decimal, parts_cost: Decimal) -> None:
    """Raise ValueError if any financial value is invalid."""
    if parts_cost < 0:
        raise ValueError("Parts cost cannot be negative")
    if agreed_price < 0:
        raise ValueError("Agreed price cannot be negative")
