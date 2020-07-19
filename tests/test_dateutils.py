import unittest
from datetime import date

from schedaus.utils import strpdate, weekday_to_dates, calc_date_in_business_days, calc_remain_days_in_month


class TestDateutils(unittest.TestCase):
    def test_strpdate(self):
        cases = [
            (None, None),
            ("1970/1/1", date(1970, 1, 1)),
            ("1970/01/01", date(1970, 1, 1)),
        ]

        for case in cases:
            with self.subTest(input=case[0], expect=case[1]):
                actual = strpdate(case[0])
                self.assertEqual(actual, case[1])

    def test_strpdate_custom_format(self):
        cases = [
            (None, "%Y-%m-%d", None),
            ("1970-1-1", "%Y-%m-%d", date(1970, 1, 1)),
            ("1970-01-01", "%Y-%m-%d", date(1970, 1, 1)),
        ]

        for case in cases:
            with self.subTest(input=case[0:1], expect=case[2]):
                actual = strpdate(case[0], case[1])
                self.assertEqual(actual, case[2])

    def test_weekday_to_dates(self):
        start = date(2020, 4, 1)
        end = date(2020, 4, 15)
        cases = [
            ("Monday", start, end, [date(2020, 4, 6), date(2020, 4, 13)]),
            ("Tuesday", start, end, [date(2020, 4, 7), date(2020, 4, 14)]),
            ("Wednesday", start, end, [date(2020, 4, 1), date(2020, 4, 8), date(2020, 4, 15)]),
            ("Friday", start, end, [date(2020, 4, 3), date(2020, 4, 10)]),
            ("Saturday", start, end, [date(2020, 4, 4), date(2020, 4, 11)]),
            ("Sunday", start, end, [date(2020, 4, 5), date(2020, 4, 12)]),
            ("m", start, end, []),
            ("s", start, end, []),
            ("XXX", start, end, []),
            ("", start, end, []),
        ]

        for case in cases:
            with self.subTest(input=case[0:3], expect=case[3]):
                actual = weekday_to_dates(*case[0:3])
                self.assertEqual(actual, case[3])

    def test_calc_date_in_business_days(self):
        cases = [
            (date(2020, 4, 1), 10, [], date(2020, 4, 10)),
            (date(2020, 4, 1), 10, [date(2020, 4, 5)], date(2020, 4, 11)),
            (date(2020, 4, 1), 10, [date(2020, 4, 4), date(2020, 4, 5)], date(2020, 4, 12)),
            (date(2020, 4, 1), 10, [date(2020, 4, 10)], date(2020, 4, 11)),
            (date(2020, 4, 1), 10, [date(2020, 4, 11)], date(2020, 4, 10)),
            (date(2020, 4, 6), -2, [date(2020, 4, 4), date(2020, 4, 5)], date(2020, 4, 3)),
            (date(2020, 4, 2), 1, [date(2020, 4, 1), date(2020, 4, 3)], date(2020, 4, 2)),
            (date(2020, 4, 2), -1, [date(2020, 4, 1), date(2020, 4, 3)], date(2020, 4, 2)),
            (date(2020, 4, 2), 2, [date(2020, 4, 2), date(2020, 4, 3)], date(2020, 4, 5)),
            (date(2020, 4, 3), -2, [date(2020, 4, 2), date(2020, 4, 3)], date(2020, 3, 31)),
        ]

        for case in cases:
            with self.subTest(input=case[0:3], expect=case[3]):
                actual = calc_date_in_business_days(*case[0:3])
                self.assertEqual(actual, case[3])

    def test_calc_remain_days_in_month(self):
        cases = [
            (date(2020, 4, 1), 30),
            (date(2020, 4, 30), 1),
            (date(2020, 2, 28), 2),
        ]

        for case in cases:
            with self.subTest(input=case[0], expect=case[1]):
                actual = calc_remain_days_in_month(case[0])
                self.assertEqual(actual, case[1])
