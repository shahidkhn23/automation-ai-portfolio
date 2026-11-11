# Coding Assistant Evaluation

A reproducible way to compare AI coding assistants (e.g. GitHub Copilot, Claude Code, ChatGPT) on the **same tasks**, with **hidden tests**, a **security scan** and an **enterprise-fit rubric**, instead of judging them by feel.

The question a company actually has is not "which assistant is smartest?" but: *which one writes correct, secure code for our kind of work, and can be run in a controlled, governed way?* This project turns that into numbers.

## How it works

```
tasks/<task>/PROMPT.md   ──►  same prompt to every assistant, fresh session
                                     │
submissions/<assistant>/<task>.py  ◄─┘  code exactly as the assistant wrote it
                                     │
evaluate.py  ──►  hidden tests (isolated, with timeout) + security scan
                                     │
RUBRIC.md    ──►  + manual criteria (rework, readability) + enterprise fit
                                     ▼
                       comparison table per assistant and task
```

## The tasks

Five small tasks that mirror everyday enterprise development, each with hidden tests that check the edge cases a careless answer misses:

| Task | Type | What the hidden tests catch |
|---|---|---|
| 01 IBAN validation | New code | Check digits (mod 97), spaces, lower case, other countries, never raising on garbage |
| 02 Fix invoice bug | Bug fixing in existing code | Discount before VAT, float rounding errors, commercial rounding, mutable default argument |
| 03 Safe order query | Security | SQL injection via the customer ID and status, quotes in names |
| 04 Retry with backoff | Reliability | Exponential delays, no retry on the wrong error type, no wait after the last attempt |
| 05 Sales report | Messy real-world data | German decimal commas, inconsistent region names, malformed rows |

## The harness checks itself

An evaluation is only worth something if it can tell good code from bad. Every task ships a correct reference solution and a deliberately broken one:

```bash
python evaluate.py --self-test
```
```
OK   01_iban_validation      reference 8/8   broken 5/8 (must fail)
OK   02_fix_invoice_bug      reference 8/8   broken 0/8 (must fail)
OK   03_safe_order_query     reference 5/5   broken 2/5 (must fail)
OK   04_retry_backoff        reference 6/6   broken 2/6 (must fail)
OK   05_sales_report         reference 4/4   broken 1/4 (must fail)
OK   security scan flags string-built SQL and passes the safe version
```

This runs in CI on every push.

## Running a comparison

1. Give each assistant the `PROMPT.md` of every task in a fresh session.
2. Save the code unchanged as `submissions/<assistant>/<task>.py`, e.g. `submissions/copilot/01_iban_validation.py`.
3. Record follow-up prompts, time and readability in `submissions/<assistant>/notes.csv` (see `RUBRIC.md`).
4. Score:

```bash
python evaluate.py submissions/copilot submissions/claude-code --json results.json
```
```
Assistant             Tasks solved  Tests passed  Security flags
copilot                     …/5             …%               …
claude-code                 …/5             …%               …
```

## Results so far

| Assistant | Tasks solved | Hidden tests passed | Security flags | Follow-up prompts |
|---|---|---|---|---|
| Claude (Opus 5.5, 11 Nov 2026) | 5/5 | 31/31 (100 %) | 0 | 0 |
| GitHub Copilot | _pending_ | | | |

How the Claude submission was made: the model got only the five `PROMPT.md` files, never `test_task.py` or `reference/`, and each answer was saved unchanged in one attempt. Readability is left blank in `notes.csv` because a human reviewer scores it, not the model itself.

**Caveat:** the tasks and hidden tests were also written with Claude's help, so Claude may have a home advantage (it may anticipate the same edge cases it would test for). The comparison against Copilot and a human review of readability are what make the result meaningful.

## Design decisions

- **Hidden tests, same prompt.** Assistants never see the tests, so they can't be optimised for them; everyone gets the identical prompt.
- **Isolation.** Each solution runs in its own temp folder in an isolated Python process with a timeout, so a hanging or harmful answer can't affect the others.
- **Security flags are hints, not verdicts.** The pattern scan (string-built SQL, `eval`, `shell=True`, hard-coded secrets, bare `except`) marks code for a human reviewer; task 03's injection tests give the hard evidence.
- **Enterprise fit is scored separately.** Data protection, admin control, audit logs and licensing (Part B of `RUBRIC.md`) decide whether a tool can be rolled out at all, regardless of code quality.

Python 3.10+, standard library only.
