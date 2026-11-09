# Scoring rubric

An AI coding assistant is only useful in a company if its code is correct **and** the tool fits controlled, governed development processes. The rubric therefore has two parts: what the code does (measured) and how the tool can be run in an enterprise (assessed).

## Part A — Code quality on the same tasks (measured, 70 %)

| Criterion | Weight | How it is measured |
|---|---|---|
| Functional correctness | 35 % | Share of hidden tests passed (`evaluate.py`) |
| Security | 15 % | Security flags from the scan + whether the injection tests in task 03 pass |
| Rework | 10 % | Number of follow-up prompts until the solution passed (0 = first try) |
| Readability | 10 % | 1–5 by a reviewer: names, structure, no dead code, sensible comments |

Every assistant gets the identical `PROMPT.md` per task, in a fresh session, with no hints from the tests. If a solution fails, the reviewer may send at most two follow-up prompts that describe the observed problem (not the fix), and records them in `notes.csv`.

## Part B — Enterprise fit (assessed, 30 %)

Scored 1–5 from vendor documentation and admin settings, with the source noted for each score.

| Criterion | Weight | Questions |
|---|---|---|
| Data protection | 10 % | Where is code processed (EU region)? Is prompt/code data used for training? Retention period? DPA available (GDPR Art. 28)? |
| Administration & control | 8 % | Central licence and policy management, SSO, ability to restrict models, features and repositories |
| Auditability | 6 % | Usage and audit logs for admins; can generated changes be traced in reviews? |
| IP & licensing | 6 % | Filter for code matching public repositories, licence indemnity |

## notes.csv

One file per assistant in its submission folder (example format):

```csv
task,follow_up_prompts,readability_1_5,minutes_to_passing,comment
01_iban_validation,0,4,3,
02_fix_invoice_bug,1,4,6,First answer kept float rounding
```
