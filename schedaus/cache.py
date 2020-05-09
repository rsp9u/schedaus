from datetime import datetime, timedelta


class ResponseCache:
    def __init__(self, expire_min=5):
        self.caches = {}
        self.expire_min = expire_min

    def set(self, key, value):
        self._check_expire()
        self.caches[key] = (value, datetime.now() + timedelta(minutes=self.expire_min))

    def get(self, key):
        self._check_expire()
        if key in self.caches:
            return self.caches[key][0]
        else:
            return None

    def _check_expire(self):
        now = datetime.now()

        def _not_expired(expiration):
            return (now - expiration).total_seconds() < 0

        self.caches = {k: v for k, v in self.caches.items() if _not_expired(v[1])}
