import base64
import json
import logging
import os
import re

from tornado import gen, httpclient

import alphabot.bot

bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)

DESK_URL = os.getenv('DESK_URL')
if not DESK_URL:
    log.warning('Desk scripts included, but DESK_URL is missing!')

DESK_CASES_SHOW_URL = '/api/v2/cases/'

log.info('Parsing desk.py')

@bot.add_command('.*agent\/case\/([0-9]+).*$')
@gen.coroutine
def desk_case_preview(message):
    if not DESK_URL: return

    user = os.getenv('DESK_USER')
    pwd  = os.getenv('DESK_PASS')
    auth = 'Basic ' + base64.encodestring(user + ':' + pwd).strip()

    url = DESK_URL + DESK_CASES_SHOW_URL + message.regex_groups[0]

    http_client = httpclient.AsyncHTTPClient()
    response = yield http_client.fetch(
        url,
        headers={'Authorization': auth,
                 'Accept': 'application/json'})

    quote = json.loads(response.body)['blurb']
    yield message.reply(quote)
