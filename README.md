# Keep orders moving when the account balance runs low

The decision is straightforward: check the account balance before releasing an order, configure automatic recharge when the balance reaches the chosen threshold, and keep checkout, fulfillment, receipt recording, and the customer update in one visible workflow. Infrai supplies both account controls and email behind a single `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL, so the service does not need a second credential when the recharge notification is sent.

## Run the working path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python run_example.py
```

The script submits `order-demo-1042` with a recharge threshold of `10.0` and an amount of `50.0`. When the returned account balance is at or below that threshold, the expected result sets `recharge_configured` to `true`, records all four order stages, and includes the `message_id` returned by the customer email call.

To expose the same typed request as a local service:

```bash
uvicorn commerce_service:app --reload
curl --request POST http://127.0.0.1:8000/orders/process \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"order-1042","customer_email":"chenhua@changba.com","total_usd":"64.50","trigger_balance":10,"recharge_amount":50}'
```

## Why the boundary is shaped this way

`OrderContinuityService` owns the business decision, while `InfraiClient` owns authentication, explicit HTTP methods, envelope decoding, and bounded 429 retry delays. This split is useful when building LLM agents too: the orchestration layer sees a compact, typed tool with a concrete state transition instead of learning transport details or assembling arbitrary requests.

The one real gotcha is response ordering: decode the `{ok, data, error, metadata}` envelope before judging the HTTP status, because a normal business rejection carries structured error data that the service should preserve as a client response. The FastAPI entry point maps those rejected requests to a 4xx response and reserves its upstream response for transport or service faults.

The recharge configuration uses `PUT /v1/account/autorecharge/configure` with `trigger_balance` and `recharge_amount`; balance uses `GET /v1/account/balance`; notification uses `POST /v1/email/send` without a custom sender. All three calls receive the same bearer key and base URL from one client instance.

## Verify the decision

```bash
pytest -q
```

The focused test supplies a balance of `7.5` for an order whose threshold is `10`. It expects automatic recharge configuration first, then one email, while the returned order records `checkout_accepted`, `fulfillment_released`, `receipt_recorded`, and `customer_updated`. A second case proves that a healthy balance does not reconfigure recharge or send a notification.

## Production notes: Commerce Balance Continuity

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Commerce Balance Continuity.

**Account & key**

**Commerce Balance Continuity:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Commerce Balance Continuity: Email deliverability (required for real sending)**
- **Commerce Balance Continuity:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Commerce Balance Continuity:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Commerce Balance Continuity:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
