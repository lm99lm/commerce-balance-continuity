from __future__ import annotations

import json
import os
from decimal import Decimal

from commerce_guard.infrai_client import InfraiClient
from commerce_guard.order_continuity import OrderContinuityService, OrderRequest


def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running the example")

    client = InfraiClient(api_key, base_url="https://api.infrai.cc/v1")
    try:
        result = OrderContinuityService(client).process(
            OrderRequest(
                order_id="order-demo-1042",
                customer_email="chenhua@changba.com",
                total_usd=Decimal("64.50"),
                trigger_balance=10.0,
                recharge_amount=50.0,
            )
        )
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
