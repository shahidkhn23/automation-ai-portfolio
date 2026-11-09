# Build guide — Event Lead Autopilot

## 0. Prepare (10 min)
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

## 1. Trigger — Google Forms: New Form Response
Pick the form. Submit 2–3 test responses first (use `../test_signups.csv`) so Zapier has sample data.

## 2–3. Formatter by Zapier → Text
- Step 2: Transform *Titlecase*, input = Full name
- Step 3: Transform *Lowercase*, input = Email

## 4. Filter by Zapier
Continue only if:
- Consent question **(Text) Contains** `Yes`
- AND step 3 output **(Text) Contains** `@`

This is the GDPR gate: no consent → nothing is stored or sent.

## 5. AI by Zapier → Analyze and return data
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

## 6. Gmail → Send Email
- To: step 3 email
- Subject: `Rentora Mobility Meetup: Anmeldung bestätigt / Registration confirmed`
- Body (HTML): see `../email_templates.md` — insert `greeting` and `first_line` from step 5

## 7. Google Calendar → Add Attendee/s to Event
Event = the meetup, attendee = step 3 email. The person gets a real calendar invite.

## 8. Paths by Zapier
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
- Gmail → reminder email (template in `../email_templates.md`)

**Path B "Everyone else"** — rule: `lead_score` Less than `4` AND Type does not contain `Company`
- Google Sheets → row in `Attendees`
- Delay Until + Gmail reminder (same as above)

## 9. Test and switch on
Test each step, then publish. Submit all rows from `../test_signups.csv` through the form and check: sheet rows, Slack alerts (should be 2), emails in the right language, calendar invites, and that the "No consent" row was stopped by the filter.
