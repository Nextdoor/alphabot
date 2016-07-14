import json
import logging

from tornado import gen
from tornado import web

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


class SlackButtonAction(web.RequestHandler):

    def get(self):
        self.write('get')

    def post(self):
        # https://api.slack.com/docs/message-buttons#responding_to_message_actions
        payload = self.get_body_argument('payload')
        payload = json.loads(payload)

        log.info('Received a button action. Adding to web events.')
        bot._web_events.append({
            # For Chat class
            'text': '',
            'user': payload['user']['id'],
            'channel': payload['channel']['id'],

            # For event listeners
            'type': 'message-action',
            'callback_id': payload['callback_id'],

            # Original data
            'payload': payload
        })


@bot.on_start
@gen.coroutine
def start_webapp():
    log.info('Creating a web app')
    app = web.Application([
        (r'/slack-button-action', SlackButtonAction)
    ])
    log.info('Listening on port 8000')
    app.listen(8000)
