from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from commerce_guard.infrai_client import InfraiClient, InfraiError
from commerce_guard.order_continuity import (
    OrderContinuityService,
    OrderRequest,
    OrderResult,
)

app = FastAPI(title="Commerce continuity service")


@app.post("/orders/process", response_model=OrderResult)
def process_order(order: OrderRequest) -> OrderResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key)
    try:
        return OrderContinuityService(client).process(order)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    finally:
        client.close()

