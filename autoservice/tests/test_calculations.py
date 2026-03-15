from decimal import Decimal

import pytest

from web.utils.calculations import calculate_order_financials, validate_financials


def test_normal_profit():
    r = calculate_order_financials(Decimal("1000000"), Decimal("300000"))
    assert r.profit == Decimal("700000")
    assert r.master_share == Decimal("280000.00")
    assert r.service_share == Decimal("420000.00")


def test_zero_parts():
    r = calculate_order_financials(Decimal("500000"), Decimal("0"))
    assert r.profit == Decimal("500000")
    assert r.master_share == Decimal("200000.00")
    assert r.service_share == Decimal("300000.00")


def test_zero_profit():
    r = calculate_order_financials(Decimal("400000"), Decimal("400000"))
    assert r.profit == Decimal("0")
    assert r.master_share == Decimal("0.00")
    assert r.service_share == Decimal("0.00")


def test_negative_profit():
    r = calculate_order_financials(Decimal("200000"), Decimal("350000"))
    assert r.profit == Decimal("-150000")
    assert r.master_share == Decimal("-60000.00")
    assert r.service_share == Decimal("-90000.00")


def test_rounding():
    r = calculate_order_financials(Decimal("1000001"), Decimal("333334"))
    assert r.master_share == round((r.profit * Decimal("0.40")), 2)
    assert r.service_share == round((r.profit * Decimal("0.60")), 2)
    # Verify two decimal places
    assert r.master_share == r.master_share.quantize(Decimal("0.01"))
    assert r.service_share == r.service_share.quantize(Decimal("0.01"))


def test_validate_financials_negative_parts():
    with pytest.raises(ValueError, match="Parts cost"):
        validate_financials(Decimal("100000"), Decimal("-1"))


def test_validate_financials_negative_price():
    with pytest.raises(ValueError, match="Agreed price"):
        validate_financials(Decimal("-1"), Decimal("0"))


def test_validate_financials_valid():
    validate_financials(Decimal("100000"), Decimal("50000"))
