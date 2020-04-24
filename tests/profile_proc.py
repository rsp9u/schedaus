import unittest
import yaml
import cProfile
import pstats

from schedaus.proc import Resolver
from tests.data import example_yaml


class ProfileProc(unittest.TestCase):
    def test_profile(self):
        d = yaml.safe_load(example_yaml)
        pr = cProfile.Profile()
        pr.enable()
        Resolver().resolve(d)
        pr.disable()
        st = pstats.Stats(pr)
        st.sort_stats("cumtime")
        st.print_stats(0.1)
