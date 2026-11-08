# Event Lead Autopilot — Zapier + AI

A Zapier automation that handles everything after someone signs up for an event (a fictional recruiting/customer event of the car-rental company): **cleaning the data, GDPR consent check, AI lead scoring, a personalised confirmation in German or English, calendar invite, sales alert for hot leads, and a reminder the day before.**

The problem: marketing teams copy sign-ups from forms into spreadsheets by hand, send generic emails, and sales finds out about interesting companies days later.

![Zap diagram](docs/zap-diagram.png)

<!-- After building: add docs/zap-overview.png, a screenshot of the real Zap -->

## The Zap (10 steps)

```
1  Google Forms      New Form Response
2  Formatter         Text → Titlecase (name)
3  Formatter         Text → Lowercase (email)
4  Filter            Only continue if consent = "Yes" and email contains "@"
5  AI by Zapier      Score lead + write personal first line (DE/EN)
6  Gmail             Send confirmation email (language from step 5)
7  Google Calendar   Add attendee to the event
8  Paths
   ├─ A "Hot lead"   (lead_score ≥ 4 OR type = Company)
   │     8A.1 Google Sheets  Create row in tab "Hot Leads"
   │     8A.2 Slack          Message to #sales-leads
   │     8A.3 Delay Until    1 day before event
   │     8A.4 Gmail          Reminder email
   └─ B "Everyone else"
         8B.1 Google Sheets  Create row in tab "Attendees"
         8B.2 Delay Until    1 day before event
         8B.3 Gmail          Reminder email
```

## Build guide

### 0. Prepare (10 min)
- **Google Form** "Rentora Mobility Meetup — Anmeldung / Registration" with these questions:
  1. Full name (short answer, required)
  2. Email (short answer, required)
  3. Preferred language / Bevorzugte Sprache (multiple choice: Deutsch, English)
  4. I am a… / Ich bin… (multiple choice: Student, Professional, Company / Unternehmen)
  5. Company or university (short answer)
  6. What do you want to get out of the event? (paragraph)
  7. I agree that my data is used to organise this event (checkbox: Yes) — *required*
- **Google Sheet** "Event Leads" with tabs `Hot Leads` and `Attendees`, header row:
  `Timestamp, Name, Email, Language, Type, Organisation, Lead score, Reason, Goal`
- **Google Calendar** event "Rentora Mobility Meetup", e.g. 2026-12-10 18:00
- Slack workspace with a channel `#sales-leads` (a free workspace is fine)

### 1. Trigger — Google Forms: New Form Response
Pick the form. Submit 2–3 test responses first (use `test_signups.csv`) so Zapier has sample data.

### 2–3. Formatter by Zapier → Text
- Step 2: Transform *Titlecase*, input = Full name
- Step 3: Transform *Lowercase*, input = Email

### 4. Filter by Zapier
Continue only if:
- Consent question **(Text) Contains** `Yes`
- AND step 3 output **(Text) Contains** `@`

This is the GDPR gate: no consent → nothing is stored or sent.

### 5. AI by Zapier → Analyze and return data
Inputs: name, type, organisation, goal, language.
Prompt:
```
You help the marketing team of a car rental company qualify event sign-ups.
Return:
- lead_score: integer 1-5. 5 = company that could become a B2B customer or partner,
  4 = professional in mobility/travel/fleet, 3 = professional elsewhere,
  2 = student with a clear goal, 1 = unclear.
- reason: one short English sentence why.
- first_line: one warm, specific sentence for the confirmation email that refers to
  what they want from the event. Write it in German if language is "Deutsch",
  otherwise English. No exclamation marks, no emojis.
- greeting: "Hallo {first name}," for Deutsch, "Hi {first name}," for English.
```
Output fields: `lead_score` (number), `reason`, `first_line`, `greeting`.

### 6. Gmail → Send Email
- To: step 3 email
- Subject: `Rentora Mobility Meetup: Anmeldung bestätigt / Registration confirmed`
- Body (HTML): see `email_templates.md` — insert `greeting` and `first_line` from step 5

### 7. Google Calendar → Add Attendee/s to Event
Event = the meetup, attendee = step 3 email. The person gets a real calendar invite.

### 8. Paths by Zapier
**Path A "Hot lead"** — rule: step 5 `lead_score` (Number) Greater than `3` **OR** Type (Text) Contains `Company`
- Google Sheets → Create Spreadsheet Row in `Hot Leads`, map all columns
- Slack → Send Channel Message to `#sales-leads`:
  ```
  :fire: Hot lead for the Mobility Meetup
  *{name}* ({type}, {organisation}) — score {lead_score}/5
  Why: {reason}
  Goal: {goal}
  ```
- Delay by Zapier → Delay Until: `2026-12-09 18:00` (24 h before the event)
- Gmail → reminder email (template in `email_templates.md`)

**Path B "Everyone else"** — rule: `lead_score` Less than `4` AND Type does not contain `Company`
- Google Sheets → row in `Attendees`
- Delay Until + Gmail reminder (same as above)

### 9. Test and switch on
Test each step, then publish. Submit all rows from `test_signups.csv` through the form and check: sheet rows, Slack alerts (should be 2), emails in the right language, calendar invites, and that the "No consent" row was stopped by the filter.

## What to put on GitHub / in your portfolio
Zapier can't export a Zap as a file, so document it:
- `docs/zap-overview.png` — the whole Zap
- `docs/ai-step.png` — the AI prompt and output fields
- `docs/slack-alert.png`, `docs/email-de.png`, `docs/email-en.png` — results
- A 60–90 second Loom video walking through one sign-up end to end

## Results
_Fill in after testing, e.g. "6 test sign-ups: 1 blocked by consent filter, 2 routed to sales, 5 confirmations sent in the right language, ~25 s from form to inbox."_

## Plan note
Zapier's free plan only runs two-step Zaps. Build this during the 14-day Professional trial, take screenshots and the video, then turn it off. A two-step version that keeps running on the free plan: *Google Forms → Google Sheets*.
