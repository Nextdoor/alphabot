import os
import json
import logging

from tornado import gen
from tornado import web

import alphabot.bot

bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)

SLACK_PORT = int(os.getenv('SLACK_PORT', 8000))
SLACK_PORT_SSL = int(os.getenv('SLACK_PORT_SSL', 8443))


@bot.on(ok=False, error={"code": -1,
                         "msg": "slow down, too many messages..."})
@gen.coroutine
def slack_throttle(event):
    log.warning('Detected a slow-down warning!')
    bot._too_fast_warning = True


class HealthCheck(web.RequestHandler):

    def get(self):
        self.write('ok')


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

        # Slightly hacky: ping slack so that it responds with pong.
        # This will cause the get_next_message to notice the web event above.
        # Correct solution requires a lot more code.
        bot.connection.write_message(json.dumps({"id": 0, "type": "ping"}))


@bot.on_start
@gen.coroutine
def start_webapp():
    log.info('Creating a web app')
    app = web.Application([
        (r'/healthz', HealthCheck),
        (r'/slack-button-action', SlackButtonAction)
    ])

    log.info('Listening on port %s' % SLACK_PORT)
    app.listen(SLACK_PORT)
    app.listen(SLACK_PORT_SSL, ssl_options={
        "certfile": "/tmp/alphabot.pem",  # Generate these in your entrypoint
        "keyfile": "/tmp/alphabot.key"
    })
