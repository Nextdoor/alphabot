import logging

from tornado import gen

import alphabot.bot

bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)


@bot.on_schedule(minute='*')
@gen.coroutine
def check_connection():
    # TODO: figure out how to check connection and reconnect on failure.
    # yield bot.check_connection()
    pass


@bot.on(ok=False, error={"code": -1,
                         "msg": "slow down, too many messages..."})
@gen.coroutine
def slack_throttle(event):
    log.warning('Detected a slow-down warning!')
    bot._too_fast_warning = True
