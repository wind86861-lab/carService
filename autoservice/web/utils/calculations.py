from decimal import Decimal
from typing import NamedTuple


class OrderFinancials(NamedTuple):
    profit: Decimal
    master_share: Decimal
    service_share: Decimal
    master_pct: int
    service_pct: int


def master_ratio_for_earnings(total_earnings: Decimal | int) -> Decimal:
    """Return master's profit share ratio based on cumulative earnings.
    Base: 40%. >10M: 45%. >15M: 50%.
    """
    e = int(total_earnings)
    if e >= 15_000_000:
        return Decimal("0.50")
    if e >= 10_000_000:
        return Decimal("0.45")
    return Decimal("0.40")


def calculate_order_financials(
    agreed_price: Decimal, parts_cost: Decimal, master_total_earnings: int = 0,
    custom_master_pct: int | None = None,
) -> OrderFinancials:
    """Calculate profit and shares using performance-based master ratio."""
    profit = agreed_price - parts_cost
    if custom_master_pct is not None:
        ratio = Decimal(str(custom_master_pct)) / Decimal("100")
    else:
        ratio = master_ratio_for_earnings(master_total_earnings)
    master_share = (profit * ratio).quantize(Decimal("0.01"))
    service_share = (profit - master_share).quantize(Decimal("0.01"))
    master_pct = int(ratio * 100)
    return OrderFinancials(
        profit=profit,
        master_share=master_share,
        service_share=service_share,
        master_pct=master_pct,
        service_pct=100 - master_pct,
    )


def validate_financials(agreed_price: Decimal, parts_cost: Decimal) -> None:
    """Raise ValueError if any financial value is invalid."""
    if parts_cost < 0:
        raise ValueError("Parts cost cannot be negative")
    if agreed_price < 0:
        raise ValueError("Agreed price cannot be negative")
