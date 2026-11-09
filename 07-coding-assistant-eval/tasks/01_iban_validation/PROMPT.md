Write a Python module `solution.py` with a function:

```python
def validate_iban(iban: str) -> bool:
```

It returns `True` if `iban` is a valid German IBAN and `False` otherwise.

- Spaces anywhere in the input are allowed and ignored; letters may be lower or upper case.
- A German IBAN starts with `DE`, has exactly 22 characters (without spaces), and has only digits after the country code.
- The check digits must be correct according to the ISO 13616 mod-97 rule.
- Never raise an exception: any invalid input, including an empty string, returns `False`.

Use only the Python standard library.
