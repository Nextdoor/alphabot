from datetime import datetime
from pytz import timezone
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

DESK_CASES = '/api/v2/cases/'
DESK_CASES_SEARCH = '/api/v2/cases/search'
DESK_CASES_SEARCH_PARAMS = 'per_page=1&sort_field=received_at&sort_direction=asc'

log.info('Parsing desk.py')

def get_basic_auth():
    user = os.getenv('DESK_USER')
    pwd  = os.getenv('DESK_PASS')
    auth = 'Basic ' + base64.encodestring(user + ':' + pwd).strip()

    return auth

def one_pm_pacific_epoch():
    pacific = timezone('US/Pacific')
    dt = pacific.localize(datetime.now())
    dt = dt.replace(hour=13)
    return dt.strftime('%s')

@bot.add_command('.*agent\/case\/([0-9]+).*$')
@gen.coroutine
def desk_case_preview(message):
    if not DESK_URL:
        message.reply('Desk URL was not provided.')
        return

    auth = get_basic_auth()
    url = DESK_URL + DESK_CASES + message.regex_groups[0]

    http_client = httpclient.AsyncHTTPClient()
    response = yield http_client.fetch(
        url,
        headers={'Authorization': auth,
                 'Accept': 'application/json'})

    quote = json.loads(response.body)['blurb']
    yield message.reply(quote)


@bot.add_command('queue status', direct=True)
@gen.coroutine
def desk_queue_status(message):
    if not DESK_URL:
        message.reply('Desk URL was not provided.')
        return

    auth = get_basic_auth()
    url_base = DESK_URL + DESK_CASES_SEARCH + '?' + DESK_CASES_SEARCH_PARAMS


    queries = {
        'HP': 'q=assigned:unassigned+group:support+priority:8,9,10+status:new,open',
        'total': 'q=assigned:unassigned+group:support+status:new,open',
        'totalOKR': 'q=(ticket_customer.updated_at:[-57600+TO+'+one_pm_pacific_epoch()+'])+assigned:NONE+group:Support+status:new,open'
    }

    responses={}
    http_client = httpclient.AsyncHTTPClient()
    for key, query in queries.items():
        url = url_base + '&' + query
        responses[key] = http_client.fetch(url, headers={'Authorization': auth,
                                                         'Accept': 'application/json'}) 
        log.info('Fetch is %s' % responses[key])

    for key, future in responses.items():
        responses[key] = yield future
        responses[key] = json.loads(responses[key].body)

    hp = responses['HP']['total_entries']
    total = responses['total']['total_entries']
    total_okr = responses['totalOKR']['total_entries']
    yield message.reply('HP count: %s. Total: %s. Total OKR: %s ' % (
        hp, total, total_okr))
