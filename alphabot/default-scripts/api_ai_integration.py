import json
import logging
import os

import apiai
from tornado import gen

import alphabot.bot

bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)

API_AI_KEY = os.getenv('API_AI_KEY')


@gen.coroutine
def fetch_from_apiai(message):
    just_text = (
        message.text
               .replace('@%s' % bot._user_name, '')
               .replace('<@%s>' % bot._user_id, '')
    )

    ai = apiai.ApiAI(API_AI_KEY)

    request = ai.text_request()
    request.query = just_text
    response = json.loads(request.getresponse().read())

    result = response['result']

    if not result['action'].startswith('alphabot'):
        raise gen.Return()

    action = result['action']
    payload = dict(message.raw)

    # prevent event recursion by removing the message type and firing an API
    # TODO: See if api.ai can provide a new message "value" to fire off.  then
    # no need for api-specific action. Just changing a message to something
    # that the bot already knows how to handle.
    payload.pop('type')
    payload.update({'api': action})

    bot._event(payload)


if not API_AI_KEY:
    log.warning('api.ai skipped since API_AI_KEY is missing.')
else:
    bot.add_command('<@%s>.*' % bot._user_id)(fetch_from_apiai)
    bot.add_command('@%s.*' % bot._user_name)(fetch_from_apiai)
