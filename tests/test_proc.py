import unittest
import yaml
from datetime import date

from schedaus.proc import Resolver
from tests.data import example_yaml


class TestProc(unittest.TestCase):
    def setUp(self):
        d = yaml.safe_load(example_yaml)
        self.result = Resolver().resolve(d)

    def test_schedule_to_drawing(self):
        self.assertEqual(self.result["calendar"].start, date(2020, 4, 1))
        self.assertEqual(self.result["calendar"].end, date(2020, 5, 15))
        self.assertEqual(self.result["calendar"].today, date(2020, 4, 20))
        self.assertEqual(len(self.result["calendar"].closed), 13)

        names = {sc.name for sc in self.result["schedules"]}
        self.assertEqual(names, {"TK1", "TK2", "task1", "task2", "task3", "task4", "task5", "milestone1"})

    def test_calculate_plan_dates(self):
        sc = {sc.name: sc for sc in self.result["schedules"]}
        expected = {
            "TK1": ((2020, 4, 10), (2020, 4, 24)),
            "TK2": ((2020, 4, 27), (2020, 5, 11)),
            "task1": ((2020, 4, 1), (2020, 4, 6)),
            "task2": ((2020, 4, 7), (2020, 4, 9)),
            "task3": ((2020, 4, 10), (2020, 5, 15)),
            "task4": ((2020, 4, 10), (2020, 4, 17)),
            "task5": ((2020, 4, 9), (2020, 4, 22)),
        }
        for name, plan in expected.items():
            with self.subTest(name=name, plan=plan):
                start = date(*plan[0])
                end = date(*plan[1])
                self.assertEqual(sc[name].plan_start, start)
                self.assertEqual(sc[name].plan_end, end)


class TestProcUtils(unittest.TestCase):
    def test_get_colors(self):
        cases = [
            (
                {"task": "green"},
                {"task": {"plan_fill": "green"}}
            ),
            (
                {"task": "green/blue/red/black/white"},
                {"task": {
                    "plan_fill": "green",
                    "plan_outline": "blue",
                    "text": "red",
                    "actual_fill": "black",
                    "actual_outline": "white"
                }}
            ),
            (
                {"task": "green", "milestone": "green"},
                {"task": {"plan_fill": "green"}, "milestone": {"plan_fill": "green"}}
            ),
            (
                {"task": "green"},
                {"milestone": {"plan_fill": "yellowgreen"}}
            ),
        ]

        for case in cases:
            with self.subTest(colors=case[0], expected=case[1]):
                actual = Resolver()._get_colors({"color": case[0]})
                for kind, values in case[1].items():
                    for part, expected_color in values.items():
                        self.assertEqual(actual[kind][part], expected_color)
