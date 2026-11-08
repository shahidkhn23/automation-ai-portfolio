#!/usr/bin/env bash
# Sends the sample reviews to your n8n webhook one by one.
# Usage: ./send_samples.sh https://YOUR-N8N/webhook-test/review-intake
URL="${1:?Pass the webhook URL}"
python3 -c 'import json,sys; [print(json.dumps(r, ensure_ascii=False)) for r in json.load(open("sample_reviews.json"))]' |
while read -r review; do
  echo ">> $review" | cut -c1-90
  curl -s -X POST "$URL" -H "Content-Type: application/json" -d "$review"; echo; echo
done
