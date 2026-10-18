"""انواع مرتبط با پرداخت و کیف‌پول بله.

مستندات: LabeledPrice، Invoice، PreCheckoutQuery، SuccessfulPayment و Transaction.

.. note::
    واحد پول در پرداخت‌های بله «ریال» (IRR) است.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaleObject
from .users import User

__all__ = ["Invoice", "LabeledPrice", "PreCheckoutQuery", "SuccessfulPayment", "Transaction"]


@dataclass
class LabeledPrice(BaleObject):
    """بخشی از قیمت کالا یا خدمت.

    مجموع مبالغِ همه‌ی اقلام، مبلغ نهایی صورتحساب را می‌سازد.
    """

    label: str
    amount: int


@dataclass
class Invoice(BaleObject):
    """پیام «درخواست پول» یا «جمع‌سپاری»."""

    title: str = ""
    description: str = ""
    total_amount: int = 0


@dataclass
class PreCheckoutQuery(BaleObject):
    """درخواست بررسی پیش از نهایی شدن پرداخت.

    بازو باید حداکثر ظرف ۱۰ ثانیه با
    :meth:`baleRobot.AsyncBaleClient.answer_pre_checkout_query` به آن پاسخ دهد.
    """

    id: str = ""
    from_user: User = field(default_factory=User, metadata={"api": "from"})
    currency: str = ""
    total_amount: int = 0
    invoice_payload: str = ""


@dataclass
class SuccessfulPayment(BaleObject):
    """رسید یک پرداخت موفق."""

    currency: str = ""
    total_amount: int = 0
    invoice_payload: str = ""
    telegram_payment_charge_id: str | None = None
    provider_payment_charge_id: str | None = None


@dataclass
class Transaction(BaleObject):
    """اطلاعات یک تراکنش (خروجی متد ``inquireTransaction``).

    وضعیت‌های ممکن: ``pending``، ``paid``، ``failed``، ``rejected``.
    """

    id: str = ""
    status: str = ""
    user_id: int | None = field(default=None, metadata={"api": "userID"})
    amount: int | None = None
    created_at: int | None = field(default=None, metadata={"api": "createdAt"})
