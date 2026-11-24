# Shahid Saleem — Automation & AI Portfolio

[![tests](https://github.com/shahidkhn23/automation-ai-portfolio/actions/workflows/tests.yml/badge.svg)](https://github.com/shahidkhn23/automation-ai-portfolio/actions/workflows/tests.yml)

Seven projects in automation and applied AI, with a focus on **making AI reliable**: validated outputs, guardrails in code, and evaluations that measure whether things actually work.

## Start here

Short on time? Look at these two:

- **[05 Student Rights Check](https://github.com/shahidkhn23/student-rights-check)**: an AI agent that checks students' contracts and answers questions about their rights in Germany. It may only cite laws from 350 hand-verified rules, and this is enforced in code.
- **[03 Rentora Support Agent](https://github.com/shahidkhn23/rentora-support-agent)**: a bilingual support agent with tool calling, a privacy check inside the tool, and 20 evals including prompt-injection attacks. There's a 28-second demo video.

Projects 01–04 are built around one fictional company, **Rentora** (car rental, Germany): the support agent answers customers, the n8n flow listens to what they say in reviews, the Zapier flow turns event sign-ups into leads, and project 04 applies the review analysis to real public reviews. Project 05 checks contracts and answers questions about students' rights in Germany. Project 06 compares AI coding assistants on the same tasks with hidden tests. Project 07 is a small n8n flow that turns a contract text into a cancel-by date and a calendar reminder. Projects 03 and 05 live in their own repositories.

| # | Project | Tools | Problem it solves |
|---|---|---|---|
| 01 | [Customer Review Intelligence](01-n8n-review-intelligence) | n8n, LLM via a chat API, Google Sheets, Slack, Gmail | Bilingual reviews read by hand, urgent ones missed, no weekly insight |
| 02 | [Event Lead Autopilot](02-zapier-event-lead-autopilot) | Zapier, AI by Zapier, Google Forms/Sheets/Calendar, Gmail, Slack | Manual sign-up handling, generic emails, sales hears about hot leads too late |
| 03 | [Rentora Support Agent](https://github.com/shahidkhn23/rentora-support-agent) | Python, LLM API, tool calling, BM25 retrieval, 20 evals | Support questions about policies, availability and bookings in DE/EN, without leaking customer data |
| 04 | [Review Insights on Real Data](04-review-insights-real-data) | Python, LLM API (optional) | Understand a company's customers from its public reviews |
| 05 | [Student Rights Check](https://github.com/shahidkhn23/student-rights-check) | Python, rule engine, BM25 retrieval, AI agent mode, 360 tests | Students in Germany sign contracts they don't understand and don't know their rights |
| 06 | [Coding Assistant Evaluation](06-coding-assistant-eval) | Python, hidden tests, security scan, scoring rubric | Choosing an AI coding assistant for a company by evidence, not by feel |
| 07 | [Contract Deadline Guard](07-n8n-contract-deadline-guard) | n8n, webhook, JavaScript, calendar (.ics) | Missing the last day to cancel a contract because the notice period is buried in the text |

## Quality

Every push runs checks in CI. In this repo: a smoke test of the review tool and a self-test proving the coding-assistant harness tells correct code from broken code. The support agent (unit tests and 20 offline evals, including 5 prompt-injection and data-leak attacks) and Student Rights Check (360 tests) run their own CI in their repositories.

## Design decisions

**Validating AI output.** Models sometimes return wrong formats or invented values. Every AI result is checked against allowed values, with a rule-based fallback, so no review gets lost.

**Privacy rule in code, not in the prompt.** Prompts can be manipulated; code can't be talked out of a rule. The name check before sharing booking data therefore runs inside the tool, and a unit test feeds it manipulated names.

**Grounded answers.** Student Rights Check only cites laws that appear in a verified tool result; this is enforced in code, with one retry and then a fallback to the verified text.

**Evaluation before opinion.** The support agent is measured with expected tools, required facts and forbidden facts; coding assistants are measured with hidden tests on identical prompts.

**n8n vs Zapier.** Zapier is the fastest option for business users, with a huge app catalogue and per-task pricing. n8n gives more control, supports code nodes, can be self-hosted (useful for GDPR) and is cheaper at volume.

## Run everything for free

| Part | Free option |
|---|---|
| AI agent (03) | Runs offline with no key. For a real model: any chat API with a free tier, set `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` |
| n8n workflow (01) | Self-hosted n8n Community edition (Docker) + `workflow-free.json` |
| Zapier flow (02) | 14-day Professional trial (no card) |
| Review analysis (04), Student Rights Check (05), evaluation harness (06) | Run offline, no key needed |

Free tiers have rate limits and change over time.

## License

MIT, see [LICENSE](LICENSE).
