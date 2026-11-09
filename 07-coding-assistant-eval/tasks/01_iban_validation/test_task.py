import unittest

from solution import validate_iban


class IbanTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(validate_iban("DE89370400440532013000"))

    def test_valid_with_spaces_and_lowercase(self):
        self.assertTrue(validate_iban("de89 3704 0044 0532 0130 00"))

    def test_wrong_check_digits(self):
        self.assertFalse(validate_iban("DE88370400440532013000"))

    def test_typo_in_account_number(self):
        self.assertFalse(validate_iban("DE89370400440532013001"))

    def test_wrong_length(self):
        self.assertFalse(validate_iban("DE8937040044053201300"))
        self.assertFalse(validate_iban("DE893704004405320130000"))

    def test_other_country(self):
        self.assertFalse(validate_iban("GB82WEST12345698765432"))

    def test_letters_in_bban(self):
        self.assertFalse(validate_iban("DE89370400440532A13000"))

    def test_garbage_never_raises(self):
        for value in ["", "   ", "DE", "😀" * 22, "DE89-3704-0044-0532-0130-00"]:
            self.assertFalse(validate_iban(value))


if __name__ == "__main__":
    unittest.main()
