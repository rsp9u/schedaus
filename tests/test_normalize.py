import unittest

from schedaus.normalize import Normalizer


class TestNormalize(unittest.TestCase):
    def test_normalize_weekday(self):
        d = {"project": {"closed": ["su", "sat", "Wed", "Mo"]}}
        n = Normalizer()
        n.normalize(d)

        self.assertEqual(d["project"]["closed"], ["Sunday", "Saturday", "Wednesday", "Monday"])

    def test_normalize_period_in_task_plan(self):
        cases = [
            (1, 1),
            (1.5, 1.5),
            ("1", 1),
            ("1 day", 1),
            ("2 days", 2),
            ("0.5 days", 0.5),
            ("1.5 days", 1.5),
            ("1 hour", 0.125),
            ("8 hours", 1),
        ]

        for case in cases:
            with self.subTest(period=case[0], type=type(case[0]), expected=case[1]):
                d = {"task": [{"plan": {"period": case[0]}}]}
                n = Normalizer()
                n.normalize(d)

                self.assertEqual(d["task"][0]["plan"]["period"], case[1])
                self.assertTrue(isinstance(d["task"][0]["plan"]["period"], float))

    def test_normalize_period_in_others(self):
        d = {
            "task": [{"actual": {"period": "2 days"}}],
            "milestone": [{"plan": {"period": "2 days"}, "actual": {"period": "2 days"}}],
        }
        n = Normalizer()
        n.normalize(d)

        self.assertEqual(d["task"][0]["actual"]["period"], 2.0)
        self.assertTrue(isinstance(d["task"][0]["actual"]["period"], float))

        self.assertEqual(d["milestone"][0]["plan"]["period"], 2.0)
        self.assertTrue(isinstance(d["milestone"][0]["plan"]["period"], float))

        self.assertEqual(d["milestone"][0]["actual"]["period"], 2.0)
        self.assertTrue(isinstance(d["milestone"][0]["actual"]["period"], float))

    def test_normalize_progress_in_task(self):
        cases = [
            (0.1, 0.1),
            (1, 1),
            ("0.1", 0.1),
            ("1", 1),
            ("10%", 0.1),
            ("200%", 2),
            ("10 %", 0.1),
            ("0.1%", 0.001),
            ("1/5", 0.2),
            ("1/3", 0.333),
            ("1/0.5", 2),
            ("1 / 5", 0.2),
        ]

        for case in cases:
            with self.subTest(period=case[0], type=type(case[0]), expected=case[1]):
                d = {"task": [{"actual": {"progress": case[0]}}]}
                n = Normalizer()
                n.normalize(d)

                self.assertEqual(round(d["task"][0]["actual"]["progress"], 3), case[1])
                self.assertTrue(isinstance(d["task"][0]["actual"]["progress"], float))

    def test_normalize_progress_in_milestone(self):
        d = {"milestone": [{"actual": {"progress": "50%"}}]}
        n = Normalizer()
        n.normalize(d)

        self.assertEqual(d["milestone"][0]["actual"]["progress"], 0.5)
