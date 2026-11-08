# Review Insights on Real Data

This project answers the manager's first question: **"Is this real, or just practice?"**

You collect real public reviews of the company you're applying to, run this tool, and bring a one-page report to the interview: what customers complain about most, with numbers and examples, plus your own ideas.

Python only, nothing to install. Works offline (keyword rules) or with Claude for better classification.

## Step by step (about 2 hours)

### 1. Collect 40–60 reviews by hand (60–90 min)
- Sources: **Google Maps** (search the company's branches, e.g. at Munich Airport), **Trustpilot**, the **App Store / Google Play** page of their app.
- Open `data/reviews_template.csv` in Excel or Google Sheets and add one row per review:
  - `date` as YYYY-MM-DD
  - `source` (Google Maps, Trustpilot, App Store…)
  - `rating` (1–5)
  - `text` (the review, copied as written)
- **Don't copy reviewer names.** You don't need them, and leaving them out keeps it GDPR-clean.
- Take a mix: recent reviews from the last 6–12 months, good and bad. Don't only pick the angry ones, or your numbers will be wrong.
- Collect by hand. Don't use scraping tools; most review sites forbid that in their terms.
- Save as **CSV UTF-8** as `data/reviews.csv`.

### 2. Run the tool (2 min)
```bash
python analyze_reviews.py data/reviews.csv --company "AurumCars"            # German report
python analyze_reviews.py data/reviews.csv --company "AurumCars" --lang en  # English report
```
With a Claude API key (`ANTHROPIC_API_KEY`), each review is classified by AI, which handles sarcasm and mixed topics much better. The report says which mode was used.

### Optional: hand-checked labels, deep dive and ideas
- **Hand-checked labels:** add columns `sentiment` and `categories` (e.g. `card_payment|car_availability`) to your CSV. If every row has them, the tool uses your labels instead of guessing, and the report says so.
- **Deep dive:** collect a second CSV with only 1–2 star reviews and add `--deep-dive complaints.csv`. Review sites are usually skewed positive, so this shows what goes wrong when something goes wrong.
- **Ideas:** write one idea per line in a text file and add `--ideas ideas.txt`. A line starting with "Einschränkung:" or "Limitation:" is shown as a note, not as an idea.
- With fewer than 10 negative reviews, the report shows counts instead of percentages, so small numbers don't look bigger than they are.

```bash
python analyze_reviews.py data/reviews.csv --company "AurumCars" --deep-dive data/complaints.csv --ideas data/ideas.txt
```

Categories: `pickup_wait`, `car_condition`, `staff`, `upsell_pressure`, `card_payment`, `deposit_damage`, `car_availability`, `support_refund`, `booking_app`, `return`, `other`.

### 3. Check the results yourself (20 min)
Open `output/aurumcars-labelled.csv` and read through the labels. Fix wrong ones by hand and run again with the corrected file if needed. The keyword rules are simple and will make mistakes. **Checking the AI's work is part of the job.** Mention it in the interview, because managers like hearing it.

### 4. Write "Meine Ideen dazu" (20 min)
Open the HTML report, and replace the yellow box with 2–3 short, concrete ideas for the top problems. Example: *"30 % of negative reviews are about waiting at pickup → test an SMS when the car is ready, so customers don't queue."* Keep it humble: you're seeing it from outside.

### 5. Print to PDF and use it
Open the report in Chrome → Print → Save as PDF. Then:
- Bring it to the interview, or attach it to your application with one sentence in the cover letter.
- Don't publish it on GitHub with the company's name. Push the tool and the sample data; keep the real report for applications.

## What to say in the interview
"I wanted to understand your customers before the interview, so I collected 50 public reviews and built a small tool to sort them. The biggest topic was X with Y %. That's a small sample, so it shows a trend, not a fact, but here's one idea I had…"

## Files
- `analyze_reviews.py` — the tool
- `data/reviews_template.csv` — empty template
- `data/SAMPLE_fake_reviews.csv` — 10 made-up reviews to test the tool (marked TEST, don't use in a report)
