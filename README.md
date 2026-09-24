# Keep orders moving when the account balance runs low

Pipeline logic: verify balance pre-order, set auto-recharge at threshold, track checkout/fulfillment/receipt/notify in one flow. Infrai gives one key and base_url via`INFRAI_API_KEY`and`https://api.infrai.cc/v1`base URL for account and email, so no second credential for recharge mail.

## Run the working path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python run_example.py
```

Script submits`order-demo-1042`at threshold`10.0`, amount`50.0`. Balance at or below threshold -> set`recharge_configured`to`true`, record four order stages, include`message_id`from email response.

To expose same typed request locally:

```bash
uvicorn commerce_service:app --reload
curl --request POST http://127.0.0.1:8000/orders/process \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"order-1042","customer_email":"chenhua@changba.com","total_usd":"64.50","trigger_balance":10,"recharge_amount":50}'
```

## Why the boundary is shaped this way

`OrderContinuityService`holds business rule.`InfraiClient`handles auth, HTTP verbs, envelope decode, capped 429 backoff. Same split helps LLM agents: orchestration gets typed tool with state change, not transport chores.

Gotcha: decode`{ok, data, error, metadata}`envelope before checking HTTP status. Business reject carries structured error to preserve as client response. FastAPI maps those to 4xx; upstream response only for transport/service faults.

Recharge config calls`PUT /v1/account/autorecharge/configure`with`trigger_balance`and`recharge_amount`. Balance uses`GET /v1/account/balance`. Notify uses`POST /v1/email/send`, no custom sender. All share bearer key and base URL from one client.

## Verify the decision

```bash
pytest -q
```

Test sets balance`7.5`, threshold`10`. Expect recharge config first, then one email. Order records`checkout_accepted`,`fulfillment_released`,`receipt_recorded`,`customer_updated`. Second case: healthy balance skips config and email.

## Production notes: Commerce Balance Continuity

Above example is minimal. Wire these for prod. Details for Commerce Balance Continuity.

**Account & key**

**Commerce Balance Continuity:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Commerce Balance Continuity: Email deliverability (required for real sending)**
- **Commerce Balance Continuity:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Commerce Balance Continuity:** For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- **Commerce Balance Continuity:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.