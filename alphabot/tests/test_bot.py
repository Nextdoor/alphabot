from tornado import testing

from alphabot import bot


class TestBot(testing.AsyncTestCase):

    @testing.gen_test
    def test_bot(self):
        testbot = bot.Bot()
