import logging

from tornado import gen

log = logging.getLogger(__name__)

class Memory():
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


class Memory_Dict(Memory):
    """Ephemeral in-memory storage."""

    def __init__(self):
        self.values = {}

    @gen.coroutine
    def _save(self, key, value):
        self.values[key] = value

    @gen.coroutine
    def _get(self, key, default):
        raise gen.Return(self.values.get(key, default))
