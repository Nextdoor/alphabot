import base64
import json
import logging
import os
import re

from tornado import gen, httpclient

log = logging.getLogger(__name__)

DESK_URL = os.getenv('DESK_URL')
CASES_SHOW_URL = '/api/v2/cases/'

@gen.coroutine
def hear(text, chat):
    if not DESK_URL: return
    match = re.match('.*agent\/case\/([0-9]+).*$', text)
    if not match: return 

    user = os.getenv('DESK_USER')
    pwd  = os.getenv('DESK_PASS')
    auth = 'Basic ' + base64.encodestring(user + ':' + pwd).strip()

    url = DESK_URL + CASES_SHOW_URL + match.groups()[0]

    http_client = httpclient.AsyncHTTPClient()
    response = yield http_client.fetch(
        url,
        headers={'Authorization': auth,
                 'Accept': 'application/json'})

    quote = json.loads(response.body)['blurb']
    chat.reply(quote)
