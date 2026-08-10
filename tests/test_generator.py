import unittest

from src.generator import format_date


class FormatDateTest(unittest.TestCase):
    def test_formats_full_and_month_dates(self):
        self.assertEqual(format_date('2023-11-01'), 'Nov 2023')
        self.assertEqual(format_date('2024-06'), 'Jun 2024')

    def test_preserves_year_present_and_unknown_values(self):
        self.assertEqual(format_date('2019'), '2019')
        self.assertEqual(format_date('Present'), 'Present')
        self.assertEqual(format_date('Expected 2027'), 'Expected 2027')


if __name__ == '__main__':
    unittest.main()
