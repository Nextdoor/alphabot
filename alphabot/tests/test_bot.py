from tornado import testing

from alphabot import bot as AB
from alphabot.tests.helper import mock_tornado

import logging
log = logging.getLogger(__name__)


class TestBot(testing.AsyncTestCase):

    @testing.gen_test
    def test_get_instance(self):
        bot = AB.get_instance()
        bot2 = AB.get_instance()

        assert(id(bot) == id(bot2))


    @testing.gen_test
    def test_setup(self):
        bot = AB.Bot()
        bot._setup_memory = mock_tornado()
        bot._setup = mock_tornado()
        bot._gather_scripts = mock_tornado()
        yield bot.setup('unit-memory', 'unit-scripts')

        self.assertEquals(bot._setup_memory.call_count, 1)

    def test_check_event_kwargs(self):
        bot = AB.Bot()
        event = {'test': 'test', 'foobar': ['one', 'two']}
        kwargs = {'test': 'test', 'foobar': ['one', 'two']}
        self.assertTrue(bot.check_event_kwargs(event, kwargs))

        event = {'type': 'message', 'message': 'Hello!'}
        kwargs = {'type': 'message',}
        self.assertTrue(bot.check_event_kwargs(event, kwargs))

        event = {'test': 'test', 'foobar': ['one', 'two'], 'extra':'yes'}
        kwargs = {'test': 'test', 'foobar': ['one', 'two']}
        self.assertTrue(bot.check_event_kwargs(event, kwargs))

        event = {'test': 'test'}
        kwargs = {'test': 'test', 'foobar': ['one', 'two']}
        self.assertFalse(bot.check_event_kwargs(event, kwargs))
