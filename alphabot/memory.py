import logging
import os

from tornado import gen

import redis

log = logging.getLogger(__name__)


class Memory(object):
    """Memory interface to Alphabot."""

    @gen.coroutine
    def save(self, key, value):
        # TODO: Add checks / hashing to prevent bad keys from breaking
        yield self._save(key, value)

    @gen.coroutine
    def get(self, key, default=None):
        value = yield self._get(key, default)
        raise gen.Return(value)

    @gen.coroutine
    def setup(self):
        yield self._setup()

    @gen.coroutine
    def _setup(self):
        log.debug('Memory engine %s does not require any setup.' % (
            self.__class__.__name__))


class MemoryDict(Memory):
    """Ephemeral in-memory storage."""

    def __init__(self):
        self.values = {}

    @gen.coroutine
    def _save(self, key, value):
        self.values[key] = value

    @gen.coroutine
    def _get(self, key, default):
        raise gen.Return(self.values.get(key, default))


class MemoryRedis(Memory):
    """Redis storage."""

    def __init__(self):
        host = os.getenv('REDIS_HOST', 'localhost')
        port = os.getenv('REDIS_PORT', 6379)
        db = os.getenv('REDIS_DB', 0)
        self.r = redis.StrictRedis(host, port, db)
        # Test connection. Raises redis.exceptions.ConnectionError.
        self.r.ping()

    @gen.coroutine
    def _save(self, key, value):
        self.r.set(key, value)

    @gen.coroutine
    def _get(self, key, default=None):
        value = self.r.get(key) or default
        raise gen.Return(value)
