import unittest
from unittest.mock import patch, Mock
from datetime import datetime

from schedaus.cache import ResponseCache


class TestResponseCache(unittest.TestCase):
    def test_cache_expired(self):
        cache = ResponseCache()

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 0, 0, 0))):
            cache.set("key", {})

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 1, 0, 0))):
            value = cache.get("key")
            self.assertIsNone(value)

    def test_cache_not_expired(self):
        cache = ResponseCache()

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 0, 0, 0))):
            cache.set("key", {})

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 0, 3, 0))):
            value = cache.get("key")
            self.assertIsNotNone(value)

    def test_cache_not_expired_changed_expiration_time(self):
        cache = ResponseCache(expire_min=120)

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 0, 0, 0))):
            cache.set("key", {})

        with patch('schedaus.cache.datetime', Mock(now=lambda: datetime(1970, 1, 1, 1, 0, 0))):
            value = cache.get("key")
            self.assertIsNotNone(value)
