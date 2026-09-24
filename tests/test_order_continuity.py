from commerce_guard.order_continuity import OrderContinuityService, OrderRequest


class RecordingInfrai:
    def __init__(self, balance: float) -> None:
        self.balance = balance
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get_balance(self) -> dict[str, object]:
        self.calls.append(("balance", {}))
        return {"balance": self.balance}

    def configure_auto_recharge(
        self, *, trigger_balance: float, recharge_amount: float
    ) -> dict[str, object]:
        self.calls.append(
            (
                "configure",
                {
                    "trigger_balance": trigger_balance,
                    "recharge_amount": recharge_amount,
                },
            )
        )
        return {"enabled": True}

    def send_email(
        self, *, to: str, subject: str, body: str
    ) -> dict[str, object]:
        self.calls.append(("email", {"to": to, "subject": subject, "body": body}))
        return {"message_id": "msg-order-1042"}


def test_low_balance_keeps_order_moving_and_notifies_customer() -> None:
    infrai = RecordingInfrai(balance=7.5)
    order = OrderRequest(
        order_id="order-1042",
        customer_email="buyer@example.com",
        total_usd="64.50",
        trigger_balance=10,
        recharge_amount=50,
    )

    result = OrderContinuityService(infrai).process(order)

    assert result.recharge_configured is True
    assert result.stages == [
        "checkout_accepted",
        "fulfillment_released",
        "receipt_recorded",
        "customer_updated",
    ]
    assert result.notification_message_id == "msg-order-1042"
    assert [name for name, _ in infrai.calls] == ["balance", "configure", "email"]


def test_healthy_balance_does_not_reconfigure_or_notify() -> None:
    infrai = RecordingInfrai(balance=25)
    order = OrderRequest(
        order_id="order-2048",
        customer_email="buyer@example.com",
        total_usd="20.00",
        trigger_balance=10,
        recharge_amount=50,
    )

    result = OrderContinuityService(infrai).process(order)

    assert result.recharge_configured is False
    assert result.notification_message_id is None
    assert [name for name, _ in infrai.calls] == ["balance"]
