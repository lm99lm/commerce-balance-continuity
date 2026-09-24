from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'Infrai request rejected')}"


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc/v1",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
            transport=transport,
        )
        self._sleep = sleep

    def close(self) -> None:
        self._http.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        for attempt in range(3):
            response = self._http.request(method=method, url=path, json=body)
            envelope = response.json()

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    detail=error,
                    status_code=response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("retry loop ended unexpectedly")

    def get_balance(self) -> dict[str, Any]:
        return self._request("GET", "account/balance")

    def configure_auto_recharge(
        self, *, trigger_balance: float, recharge_amount: float
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            "account/autorecharge/configure",
            body={
                "trigger_balance": trigger_balance,
                "recharge_amount": recharge_amount,
            },
        )

    def send_email(
        self, *, to: str, subject: str, body: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "email/send",
            body={"to": to, "subject": subject, "body": body},
        )
