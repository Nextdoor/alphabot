import logging
import sys

from tornado import ioloop, gen
import requests

import alphabot.bot

requests.packages.urllib3.disable_warnings()

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)
logging.captureWarnings(True)
log = logging.getLogger(__name__)

def start_ioloop():
    try:
        ioloop.IOLoop.instance().run_sync(start_alphabot)
    except KeyboardInterrupt:
        pass
    except alphabot.bot.AlphaBotException as e:
        log.critical('Alphabot failed. Reason: %s' % e)

@gen.coroutine
def start_alphabot():

    # Add slack-specific adapter separater.
    bot = alphabot.bot.get_instance()

    yield bot.connect()
    yield bot.gather_scripts()
    yield bot.start()

if __name__ == '__main__':
    start_ioloop()
