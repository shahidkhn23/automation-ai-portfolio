# Shahid — Automation & AI Portfolio

Five projects around one fictional company, **Rentora** (car rental, Germany). In the first three, the support agent answers customers, the n8n flow listens to what they say in reviews, and the Zapier flow turns event sign-ups into leads. The last two take this into the real world: analysing real public reviews, and running a pilot with a real business.

| # | Project | Tools | Business problem |
|---|---|---|---|
| 01 | [Customer Review Intelligence](01-n8n-review-intelligence) | n8n, LLM via Groq (free) or OpenAI, Google Sheets, Slack, Gmail | Bilingual reviews read by hand, urgent ones missed, no weekly insight |
| 02 | [Event Lead Autopilot](02-zapier-event-lead-autopilot) | Zapier, AI by Zapier, Google Forms/Sheets/Calendar, Gmail, Slack | Manual sign-up handling, generic emails, sales hears about hot leads too late |
| 03 | [Rentora Support Agent](03-ai-support-agent) | Python, Claude API, tool calling, BM25 retrieval, evals | Support questions about policies, availability and bookings in DE/EN |
| 04 | [Review Insights on Real Data](04-review-insights-real-data) | Python, Claude API (optional) | Understand a real company's customers from public reviews before the interview |
| 05 | [Real Pilot Kit](05-real-pilot-kit) | Process, German templates | Get a real business to use project 01 or 02 for 3 weeks, measure it, get a reference |

**Projects 01–03 show you can build. 04 and 05 show it works in the real world.** That's what a manager is really asking about.

---

## Run everything for free

| Part | Free option |
|---|---|
| AI agent (03) | Runs offline with no key. For a real model: free Groq key (`GROQ_API_KEY`), no credit card |
| n8n workflow (01) | Self-hosted n8n Community edition (Docker) + `workflow-free-groq.json` |
| Zapier flow (02) | Build it during the 14-day Professional trial (no card) |
| Review analysis (04) | Runs offline, no key needed |
| Videos | Loom free plan (5 min per video, 25 videos) or OBS Studio |

Free tiers have rate limits and change over time. Check the provider's page if something stops working.

## Before you apply: checklist

1. Put each project in its own **public GitHub repo** (or one repo with three folders, like this one).
2. **Actually run each one** and replace every `_Fill in…_` line with your real numbers. Never put a number on your CV that you didn't measure.
3. Add screenshots to `docs/` and record a **60–90 s Loom** per project. Recruiters click videos, not code.
4. Pin the repos on your GitHub profile and add the link to your CV header and LinkedIn "Featured".
5. Change things so they're yours: swap "Rentora" for a scenario from the job ad, add one feature from the "Next steps" lists.

---

## CV section

### Deutsch

**Projekte (Automatisierung & KI)**

**KI-Kundensupport-Agent** · Python, Claude API, Tool Calling | github.com/…
- Zweisprachigen (DE/EN) KI-Agenten für eine Autovermietung entwickelt, der Mietbedingungen, Verfügbarkeiten und Buchungen über 4 Tools abfragt statt zu raten
- Datenschutz-Guardrail umgesetzt: Buchungsdaten nur bei passendem Nachnamen; Eskalation an Mitarbeitende bei Unfällen und Beschwerden
- Evaluations-Suite mit 15 Testfällen aufgebaut (Tool-Auswahl, Fakten, Datenlecks); Ergebnis: _X/15_

**Review-Intelligence-Workflow** · n8n, LLM (Groq/OpenAI), Google Sheets, Slack | github.com/…
- n8n-Workflow, der deutsche und englische Kundenbewertungen automatisch nach Stimmung, Kategorie und Dringlichkeit klassifiziert und Antwortentwürfe erstellt
- Dringende Fälle (Sicherheit, rechtliche Drohungen) lösen sofort Slack-Alerts aus; Fallback-Logik bei KI-Fehlern
- Wöchentliches KI-Briefing per E-Mail mit Kennzahlen nach Filiale und Kategorie für das Produktteam

**Event-Lead-Automatisierung** · Zapier, AI by Zapier, Google Workspace | Video: loom.com/…
- 10-stufigen Zap gebaut: DSGVO-Einwilligungsfilter, KI-Lead-Scoring, personalisierte Bestätigung auf DE/EN, Kalendereinladung, Erinnerung
- Hot Leads (Score ≥ 4) automatisch an den Vertrieb über Slack weitergeleitet

### English

**Projects (Automation & AI)**

**AI Customer Support Agent** · Python, Claude API, tool calling
- Built a bilingual (DE/EN) AI agent for a car rental use case that answers from 4 tools (policy search, availability, booking lookup, human handoff) instead of guessing
- Implemented a privacy guardrail in code (booking data only with matching last name) and escalation for accidents and complaints
- Wrote a 15-case evaluation suite covering tool choice, factual accuracy and data leaks; score: _X/15_

**Review Intelligence Workflow** · n8n, LLM (Groq/OpenAI), Google Sheets, Slack
- Automated classification of German and English reviews by sentiment, category and urgency, with reply drafts in the customer's language
- Real-time Slack alerts for safety and legal issues; rule-based fallback when the AI step fails
- Weekly AI-written briefing email with metrics by branch and category for the product team

**Event Lead Autopilot** · Zapier, AI by Zapier, Google Workspace
- Built a 10-step Zap with GDPR consent filter, AI lead scoring, bilingual personalised confirmations, calendar invites and reminders
- Routed hot leads (score ≥ 4) to sales via Slack automatically

---

## Interview: be ready to explain
- **Why validate AI output?** Models sometimes return wrong formats or invented values. I check against allowed values and fall back to rules, so no review gets lost.
- **Why is the name check inside the tool, not just in the prompt?** Prompts can be tricked. Code can't be talked out of a rule.
- **How do you know the agent works?** The eval suite: 15 conversations with expected tools and facts, run after every change.
- **n8n vs Zapier?** Zapier: fastest for business users, huge app catalogue, priced per task. n8n: more control, code nodes, can be self-hosted (good for GDPR), cheaper at volume.
- **What would you improve?** Pick one item from each project's "Next steps".
