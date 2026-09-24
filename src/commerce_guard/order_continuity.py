from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    order_id: str = Field(min_length=1)
    customer_email: str = Field(min_length=3)
    total_usd: Decimal = Field(gt=0)
    trigger_balance: float = Field(gt=0)
    recharge_amount: float = Field(gt=0)


class OrderResult(BaseModel):
    order_id: str
    account_balance: float
    recharge_configured: bool
    stages: list[str]
    notification_message_id: str | None


class ContinuityAPI(Protocol):
    def get_balance(self) -> dict[str, object]:
        """Return the account balance envelope data."""

    def configure_auto_recharge(
        self, *, trigger_balance: float, recharge_amount: float
    ) -> dict[str, object]:
        """Set the balance threshold and recharge amount."""

    def send_email(
        self, *, to: str, subject: str, body: str
    ) -> dict[str, object]:
        """Send an order update and return its message identifier."""


@dataclass
class OrderContinuityService:
    infrai: ContinuityAPI

    def process(self, order: OrderRequest) -> OrderResult:
        balance_data = self.infrai.get_balance()
        balance = float(balance_data["balance"])
        recharge_configured = balance <= order.trigger_balance
        message_id: str | None = None

        if recharge_configured:
            self.infrai.configure_auto_recharge(
                trigger_balance=order.trigger_balance,
                recharge_amount=order.recharge_amount,
            )
            sent = self.infrai.send_email(
                to=order.customer_email,
                subject=f"Order {order.order_id} continues after account recharge",
                body=(
                    f"Recharge is active and order {order.order_id} continues "
                    "through fulfillment and receipt delivery."
                ),
            )
            message_id = str(sent["message_id"])

        stages = ["checkout_accepted", "fulfillment_released", "receipt_recorded"]
        stages.append("customer_updated")
        return OrderResult(
            order_id=order.order_id,
            account_balance=balance,
            recharge_configured=recharge_configured,
            stages=stages,
            notification_message_id=message_id,
        )
