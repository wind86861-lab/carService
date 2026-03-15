from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


class OrderCreateSchema(BaseModel):
    brand: str
    model: str
    plate: str
    color: str
    year: int
    client_name: str
    client_phone: str
    problem: str
    work_desc: str
    agreed_price: Decimal
    paid_amount: Decimal

    @field_validator("plate")
    @classmethod
    def plate_upper(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("brand", "model")
    @classmethod
    def min2(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Minimum 2 characters")
        return v.strip()

    @field_validator("color")
    @classmethod
    def color_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Color is required")
        return v.strip()

    @field_validator("year")
    @classmethod
    def year_valid(cls, v: int) -> int:
        import datetime as dt
        current_year = dt.date.today().year
        if v < 1950 or v > current_year + 1:
            raise ValueError(f"Year must be between 1950 and {current_year + 1}")
        return v

    @field_validator("problem", "work_desc")
    @classmethod
    def min10(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Minimum 10 characters")
        return v.strip()

    @field_validator("agreed_price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Agreed price must be positive")
        return v

    @field_validator("paid_amount")
    @classmethod
    def paid_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Paid amount cannot be negative")
        return v

    @field_validator("client_name")
    @classmethod
    def client_name_min2(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Minimum 2 characters")
        return v.strip()

    @field_validator("client_phone")
    @classmethod
    def phone_uzbek(cls, v: str) -> str:
        import re
        if not re.match(r"^\+998\d{9}$", v.strip()):
            raise ValueError("Phone must match Uzbekistan format: +998XXXXXXXXX")
        return v.strip()


class OrderUpdateStatusSchema(BaseModel):
    status: str
    note: Optional[str] = None


class OrderCloseSchema(BaseModel):
    parts_cost: Decimal

    @field_validator("parts_cost")
    @classmethod
    def parts_cost_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Parts cost cannot be negative")
        return v


class PaymentSchema(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class PhotoResponse(BaseModel):
    id: int
    file_id: str
    url: str
    uploaded_at: datetime


class CarResponse(BaseModel):
    id: int
    order_number: str
    brand: Optional[str]
    model: Optional[str]
    plate: Optional[str]
    color: Optional[str]
    year: Optional[int]
    visit_count: int


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    phone: Optional[str]
    role: str


class OrderLogResponse(BaseModel):
    id: int
    status: Optional[str]
    note: Optional[str]
    changed_at: datetime


class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    client_name: Optional[str]
    client_phone: Optional[str]
    problem: Optional[str]
    work_desc: Optional[str]
    agreed_price: Decimal
    paid_amount: Decimal
    parts_cost: Decimal
    profit: Decimal
    master_share: Decimal
    service_share: Decimal
    client_confirmed: bool
    created_at: datetime
    ready_at: Optional[datetime]
    closed_at: Optional[datetime]
    car: Optional[CarResponse] = None
    logs: Optional[list[OrderLogResponse]] = None


class FinancialSummaryResponse(BaseModel):
    order_count: int
    total_price: Decimal
    total_parts: Decimal
    total_profit: Decimal
    total_master_share: Decimal


class TelegramAuthSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
