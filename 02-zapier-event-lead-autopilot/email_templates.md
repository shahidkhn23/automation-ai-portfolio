# Email templates

Use the fields from the AI step: `{greeting}`, `{first_line}`. Name and dates from the form/event.
The bilingual version below works without a second Gmail step: the personal lines adapt, the fixed text is in both languages.

## Confirmation (step 6)

**Subject:** Rentora Mobility Meetup: Anmeldung bestätigt / Registration confirmed

```html
<p>{greeting}</p>
<p>{first_line}</p>
<p><b>DE:</b> Deine Anmeldung ist bestätigt. Wir sehen uns am <b>10. Dezember 2026 um 18:00 Uhr</b>.
Eine Kalendereinladung kommt gleich separat.</p>
<p><b>EN:</b> Your registration is confirmed. See you on <b>10 December 2026 at 6 pm</b>.
A calendar invite is on its way.</p>
<p>Rentora Events Team</p>
<p style="font-size:12px;color:#888">Du hast dich mit deiner Einwilligung angemeldet. Antworte einfach mit "Abmelden", wenn wir deine Daten löschen sollen. /
You signed up with your consent. Reply "unsubscribe" and we'll delete your data.</p>
```

## Reminder (steps 8A.4 / 8B.3)

**Subject:** Morgen / Tomorrow: Rentora Mobility Meetup

```html
<p>{greeting}</p>
<p><b>DE:</b> Kurze Erinnerung: Das Meetup ist morgen um 18:00 Uhr. Wir freuen uns auf dich.</p>
<p><b>EN:</b> Quick reminder: the meetup is tomorrow at 6 pm. Looking forward to seeing you.</p>
<p>Rentora Events Team</p>
```
