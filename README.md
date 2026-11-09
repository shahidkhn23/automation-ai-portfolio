# Shahid — Automation & AI Portfolio

Six projects in automation and applied AI. The first five are built around one fictional company, **Rentora** (car rental, Germany): the support agent answers customers, the n8n flow listens to what they say in reviews, and the Zapier flow turns event sign-ups into leads. Projects 04 and 05 take this into the real world: analysing real public reviews, and running a pilot with a real business. Project 06 is independent: it checks contracts and answers questions about students' rights in Germany, based on 50 hand-verified legal rules.

| # | Project | Tools | Business problem |
|---|---|---|---|
| 01 | [Customer Review Intelligence](01-n8n-review-intelligence) | n8n, LLM via Groq (free) or OpenAI, Google Sheets, Slack, Gmail | Bilingual reviews read by hand, urgent ones missed, no weekly insight |
| 02 | [Event Lead Autopilot](02-zapier-event-lead-autopilot) | Zapier, AI by Zapier, Google Forms/Sheets/Calendar, Gmail, Slack | Manual sign-up handling, generic emails, sales hears about hot leads too late |
| 03 | [Rentora Support Agent](03-ai-support-agent) | Python, Claude API, tool calling, BM25 retrieval, evals | Support questions about policies, availability and bookings in DE/EN |
| 04 | [Review Insights on Real Data](04-review-insights-real-data) | Python, Claude API (optional) | Understand a real company's customers from its public reviews |
| 05 | [Real Pilot Kit](05-real-pilot-kit) | Process, German templates | Run project 01 or 02 with a real business for 3 weeks and measure the results |
| 06 | [Student Rights Check](06-student-rights-check) | Python, BM25 retrieval, rule engine, Claude API (optional), 50 tests | Students in Germany sign contracts they don't understand and don't know their rights |

---

## Run everything for free

| Part | Free option |
|---|---|
| AI agent (03) | Runs offline with no key. For a real model: free Groq key (`GROQ_API_KEY`), no credit card |
| n8n workflow (01) | Self-hosted n8n Community edition (Docker) + `workflow-free-groq.json` |
| Zapier flow (02) | Build it during the 14-day Professional trial (no card) |
| Review analysis (04) | Runs offline, no key needed |

Free tiers have rate limits and change over time. Check the provider's page if something stops working.

---

## Design decisions

**Validating AI output.** Models sometimes return wrong formats or invented values. Every AI result is checked against allowed values, with a rule-based fallback, so no review gets lost.

**Privacy rule in code, not in the prompt.** Prompts can be manipulated; code can't be talked out of a rule. The name check before sharing booking data therefore runs inside the tool.

**Evaluation.** The support agent has an eval suite of 15 conversations with expected tools and facts, run after every change.

**n8n vs Zapier.** Zapier is the fastest option for business users, with a huge app catalogue and per-task pricing. n8n gives more control, supports code nodes, can be self-hosted (useful for GDPR) and is cheaper at volume.
