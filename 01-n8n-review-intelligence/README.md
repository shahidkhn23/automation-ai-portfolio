# Customer Review Intelligence — n8n + LLM (Groq or OpenAI)

An n8n automation that turns raw customer reviews (German and English) into **structured data, urgent alerts and a weekly product briefing**, for a (fictional) car rental company.

The problem: reviews arrive from Google, Trustpilot and app stores in two languages. Someone reads them by hand, urgent ones (safety, legal threats) get missed, and product managers never see the patterns.

![Workflow diagram](docs/workflow-diagram.png)

**Real test run in n8n (self-hosted, Groq):** green = executed.

![n8n test run](docs/n8n-canvas-test-run.jpg)

## What it does

**Flow 1 — real-time triage (webhook)**
1. A review is POSTed to the webhook
2. Code node cleans and validates the input
3. An LLM (tested with Groq `openai/gpt-oss-120b`; OpenAI `gpt-4o-mini` in `workflow.json`) returns language, sentiment, category, urgency, an English summary and a reply draft *in the customer's language*
4. The AI output is validated against allowed values. **If the AI call fails or returns junk, a rule-based fallback is used and the review is flagged for a human**, so nothing is lost
5. The caller gets a JSON response immediately
6. Every review is logged to Google Sheets
7. Urgent reviews (safety, legal threat, 1–2 stars + negative, or AI failure) go to Slack `#customer-alerts` with the suggested reply

**Flow 2 — weekly briefing (schedule)**
Every Monday 08:00: reads the last 7 days from the sheet → counts by sentiment, category and branch → AI writes a 150-word briefing (trend, top 2 problems with numbers, one suggestion) → HTML email to the product team.

## Design decisions
- **Structured output + validation** instead of trusting free text from the model
- **Retries (3x) and continue-on-error** on the API call, with a fallback path
- **Human in the loop**: AI drafts replies, a person sends them
- Cheap model for classification; costs a fraction of a cent per review

## Run it for free
Two things normally cost money here: n8n Cloud and the OpenAI key. Both have free alternatives:
- **n8n:** the self-hosted Community edition is free. Install Docker Desktop, then run
  `docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n` and open http://localhost:5678.
- **AI model:** import **`workflow-free-groq.json`** instead of `workflow.json`. It calls Groq, which has a free tier without a credit card. Create a key at console.groq.com and use it in a *Header Auth* credential: name `Authorization`, value `Bearer gsk_...`.
- The model is set in the "Normalize & Validate" and "Build Weekly Stats" nodes (`openai/gpt-oss-120b`). If Groq has renamed or removed it, pick another model from the list at console.groq.com and change it there. If you get an error about `response_format`, delete that line in "Normalize & Validate"; the parse step already handles messy output.
- Free tiers have rate limits. Fine for testing with the sample reviews, not for thousands of reviews.

## Google Sheets on self-hosted n8n
The one-click "Sign in with Google" only exists on n8n Cloud. Self-hosted needs your own Google OAuth app (free, about 20 min):
1. Google Cloud Console: create a project, enable **Google Sheets API** and **Google Drive API**
2. Google Auth Platform: app name, audience **External** (stays in testing mode), add yourself as **test user**
3. Clients → Create → **Web application**, redirect URI `http://localhost:5678/rest/oauth2-credential/callback`
4. Paste Client ID and Client Secret into the n8n *Google Sheets OAuth2* credential → Sign in with Google. "Google hasn't verified this app" is expected for your own test app → Continue
5. In both Sheets nodes, pick the tab **From list** instead of typing its name (avoids typos)

## Setup (about 15 minutes)
1. n8n Cloud trial or self-hosted (`docker run -it --rm -p 5678:5678 n8nio/n8n`)
2. *Workflows → Import from File →* `workflow.json`
3. Credentials:
   - **OpenAI**: create a *Header Auth* credential, name `Authorization`, value `Bearer sk-...`, select it in both "AI" nodes
   - **Google Sheets**: OAuth; create a sheet with a tab named `Reviews` and paste its URL into both Sheets nodes. Add this header row:
     `review_id, received_at, source, branch, author, rating, text, language, sentiment, category, urgency, summary_en, reply_draft, ai_status, ai_error, needs_escalation`
   - **Slack** and **Gmail**: OAuth; set your channel and recipient
4. Click *Test workflow*, then send the samples:
   ```bash
   ./send_samples.sh https://YOUR-N8N/webhook-test/review-intake
   ```

`sample_reviews.json` contains 5 test reviews: a German pickup complaint, a positive English review, a German legal threat about a damage charge, an app bug, and a safety issue.

## Results (real runs, 8 and 11 Nov 2026)
Self-hosted n8n (Docker) + Groq free tier, model `openai/gpt-oss-120b`, the 5 reviews from `sample_reviews.json`. First run (8 Nov) without Google Sheets; second run (11 Nov) with **Google Sheets connected**. Slack and the Gmail send step are not connected.

| Review | AI result | Escalated |
|---|---|---|
| DE, 1★, 50 min wait at counter | negative · pickup_wait · German reply draft | yes |
| EN, 5★, quick pickup, clean car | positive · English reply draft | no |
| DE, 2★, charged for old scratch, legal threat | negative · damage_claim · urgency high | yes |
| EN, 3★, app crashes adding a driver | neutral · booking_app | no |
| EN, 1★, brake warning light, hotline unreachable | negative · car_condition · urgency high | yes |

- Escalation: 5/5 as expected. Reply language matched the review: 5/5.
- Category: 4/5 ideal. The brake review was labelled `car_condition`; `safety` would have been better. It was still escalated because urgency was high.
- One reply draft contained a placeholder (`[phone/email]`). That's why drafts go to a human before anything is posted.
- **Google Sheets (11 Nov):** all 5 reviews were appended to the sheet; the weekly flow's *Read Reviews* step read the same 5 rows back.
- **Weekly briefing (11 Nov):** the flow ran up to the finished email (subject *"Review briefing 2026-11-11: 5 reviews, avg 2.40"*, the correct average of 1+5+2+3+1). Groq wrote the summary, e.g. *"Customer satisfaction fell to 2.4 / 5, driven by long pickup waits and unaddressed safety alerts"*. Weak spot: it counted 2 "pickup wait" complaints, but one of those two reviews was positive. The stats step should pass only negative reviews per category to the AI.
- On 11 Nov the brake review was labelled `safety` (on 8 Nov: `car_condition`). Same input, different label: LLM output isn't fully deterministic, which is why the validation step exists.
- First run failed with `401 Invalid API Key` (credential typo). The fallback kicked in as designed: the review was still answered, logged and flagged instead of being lost.

## Next steps
- Pull reviews automatically from the Google Business Profile API instead of the webhook
- Approve-and-send replies from Slack buttons
- Dashboard in Looker Studio on top of the sheet
