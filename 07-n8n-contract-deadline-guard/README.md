# 07 · Contract Deadline Guard (n8n)

Rental, phone and gym contracts usually end with a notice period, and the last day to cancel is easy to miss. This workflow takes the text of a contract, finds the notice period and the end date, works out the last day to cancel, and sends back a calendar file (.ics) with a reminder 14 days before.

It runs without any account or API key. No LLM is involved: plain rules, so the result is the same every time and easy to test.

## What it does

`POST /webhook/contract-deadlines` with `{"text": "<contract text>"}` returns:

```json
{
  "notice_period": "3 Monate",
  "end_date": "2027-08-31",
  "auto_renewal": true,
  "cancel_by": "2027-05-31",
  "days_left": 188,
  "warnings": ["The contract renews automatically if you do not cancel in time."],
  "ics": "BEGIN:VCALENDAR..."
}
```

German and English texts both work (see `sample_contract_de.txt` and `sample_contract_en.txt`). Optional field `today` (YYYY-MM-DD) fixes the date, which is what the tests use.

## Run it

1. In n8n: Workflows → Import from file → `workflow.json`.
2. Activate it and call the production URL:

```bash
curl -X POST https://<your-n8n>/webhook/contract-deadlines \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Das Mietverhältnis ist befristet bis 31.08.2027. Kündigungsfrist: 3 Monate.\"}"
```

The logic itself runs without n8n: `node test.js`.

## How it is built

- `extract.js` holds all the logic. `build_workflow.py` copies it into the n8n Code node, so the tested code and the workflow code are the same.
- Three nodes: Webhook, Code, Respond to Webhook.
- Month maths clamps to the last day of the month (3 months before 31.05. is 28.02., not 31.02.).
- If something is missing (no notice period, no end date) it says so in `warnings` instead of guessing.

## Limits

- It finds dates and periods with patterns, so unusual wording can be missed. Always read the contract.
- It does not know about legal rules for specific contract types or special rights to cancel.
- General information, not legal advice.
- I validated `workflow.json` as JSON and ran the exact Code-node text in Node. I have not imported it into a running n8n instance.

To rebuild after changing the logic: `python build_workflow.py`.
