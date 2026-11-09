# Review Insights on Real Data

Turns real public customer reviews of a company into a one-page insight report: what customers complain about most, with numbers, examples and improvement ideas.

Python only, nothing to install. Works offline (keyword rules) or with Claude for better classification.

## How it works

### 1. Collect reviews
- Sources: **Google Maps** (the company's branches), **Trustpilot**, the **App Store / Google Play** page of their app.
- One row per review in `data/reviews_template.csv`:
  - `date` as YYYY-MM-DD
  - `source` (Google Maps, Trustpilot, App Store…)
  - `rating` (1–5)
  - `text` (the review, copied as written)
- **No reviewer names** are collected or stored, which keeps the data GDPR-clean.
- A balanced sample of recent reviews (last 6–12 months, positive and negative) avoids skewed numbers.
- Reviews are collected by hand, not scraped; most review sites forbid scraping in their terms.
- Saved as **CSV UTF-8** as `data/reviews.csv`.

### 2. Run the tool
```bash
python analyze_reviews.py data/reviews.csv --company "Rentora"            # German report
python analyze_reviews.py data/reviews.csv --company "Rentora" --lang en  # English report
```
With a Claude API key (`ANTHROPIC_API_KEY`), each review is classified by AI, which handles sarcasm and mixed topics much better. The report says which mode was used.

### Options: hand-checked labels, deep dive and ideas
- **Hand-checked labels:** columns `sentiment` and `categories` (e.g. `card_payment|car_availability`) in the CSV. If every row has them, the tool uses these labels instead of guessing, and the report says so.
- **Deep dive:** a second CSV with only 1–2 star reviews via `--deep-dive complaints.csv`. Review sites are usually skewed positive, so this shows what goes wrong when something goes wrong.
- **Ideas:** one idea per line in a text file via `--ideas ideas.txt`. A line starting with "Einschränkung:" or "Limitation:" is shown as a note, not as an idea.
- With fewer than 10 negative reviews, the report shows counts instead of percentages, so small numbers don't look bigger than they are.

```bash
python analyze_reviews.py data/reviews.csv --company "Rentora" --deep-dive data/complaints.csv --ideas data/ideas.txt
```

Categories: `pickup_wait`, `car_condition`, `staff`, `upsell_pressure`, `card_payment`, `deposit_damage`, `car_availability`, `support_refund`, `booking_app`, `return`, `other`.

### 3. Quality check
The labelled output (`output/<company>-labelled.csv`) is reviewed by hand. Wrong labels are corrected and the tool is run again with the corrected file. The keyword rules are simple and will make mistakes, so checking the AI's work is part of the process.

### 4. Report
The HTML report includes a section for 2–3 concrete ideas on the top problems, e.g. *"30 % of negative reviews are about waiting at pickup → test an SMS when the car is ready, so customers don't queue."* It can be saved as PDF via the browser's print dialog.

Reports on real companies are not published in this repo; only the tool and sample data are.

## Files
- `analyze_reviews.py` — the tool
- `data/reviews_template.csv` — empty template
- `data/SAMPLE_fake_reviews.csv` — 10 made-up reviews to test the tool (marked TEST)
