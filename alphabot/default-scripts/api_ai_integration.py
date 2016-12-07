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

    log.info('Requesting action from api.ai...')
    request = ai.text_request()
    request.query = just_text
    response = json.loads(request.getresponse().read())

    result = response.get('result', {})
    action = result.get('action', {})
    log.info('Got action %s' % action)
    function = bot._function_map.get(action)
    log.info('Got function %s' % function)

    if function:
        log.info('Invoking...')

        # import pdb; pdb.set_trace()
        result = yield function(message)

        log.info('Function returned %s' % result)


if not API_AI_KEY:
    log.warning('api.ai skipped since API_AI_KEY is missing.')
else:
    bot.add_command('<@%s>.*' % bot._user_id)(fetch_from_apiai)
    bot.add_command('@%s.*' % bot._user_name)(fetch_from_apiai)
