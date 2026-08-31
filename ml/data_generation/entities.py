"""Core entity definitions and generators."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import numpy as np


@dataclass
class Merchant:
    merchant_id: str
    name: str
    primary_category: str
    base_refund_rate: float


@dataclass
class Device:
    device_id: str
    device_type: str  # mobile, desktop, tablet


@dataclass
class Address:
    address_id: str
    region: str
    address_type: str  # household, hostel, office, standard


@dataclass
class PaymentToken:
    payment_token_id: str
    payment_type: str  # upi, credit_card, debit_card, netbanking


@dataclass
class Customer:
    customer_id: str
    account_created_at: datetime
    merchant_id: str
    segment: str  # standard, premium, budget, frequent_buyer
    archetype: str  # legit archetype or abuse ring type
    ring_id: Optional[str] = None
    is_abuse: bool = False
