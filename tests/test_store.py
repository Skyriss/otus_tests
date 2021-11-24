from unittest import TestCase

import fakeredis
from datetime import datetime, timedelta

from store import Store, Storage

INTERESTS = ["cars", "pets", "travel", "hi-tech", "sport", "music",
             "books", "tv", "cinema", "geek", "otus"]

server = fakeredis.FakeServer()

class TestStore(TestCase):

    def setUp(self):
        self.store = Store(Storage())
        self.server = fakeredis.FakeServer()
        self.store.redis = fakeredis.FakeRedis(server=self.server)
        self.store.set("test", "ok")

    def test_get(self):
        self.server.connected = True
        self.assertEqual(self.store.get("test"), "ok")
        self.assertIsNone(self.store.get("fake"))

    def test_set(self):
        self.store.set("test", "new ok")
        self.assertNotEqual(self.store.get("test"), "ok")
        self.assertEqual(self.store.get("test"), "new ok")

    def test_server_down(self):
        self.server.connected = False
        with self.assertRaises(ConnectionError):
            self.store.get("1-2-3-4-5")

    def test_cache_set_and_get(self):
        self.assertIsNone(self.store.cache_get("cache_test"))
        self.store.cache_set("cache_test", "test")
        self.assertEqual(self.store.cache_get("cache_test"), "test")

    def test_cache_expire(self):
        self.store.cache_set("cache_test", "expire_test", 60*60)
        self.assertEqual(self.store.cache_get("cache_test"), "expire_test")

    def test_cache_expired(self):
        self.store.cache_set("cache_test", "expire_test", 0.000001)
        self.assertIsNone(self.store.cache_get("cache_test"))
