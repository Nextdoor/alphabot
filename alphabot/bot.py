import json
import logging
import os
import pkgutil
import re
import sys
import traceback

from tornado import websocket, gen, httpclient
import requests

log = logging.getLogger(__name__)


SLACK_TOKEN=os.getenv('SLACK_TOKEN')
SLACK_START='https://slack.com/api/rtm.start'
SLACK_REACT='https://slack.com/api/reactions.add'

def get_instance():
    if not Bot.instance:
        log.debug('Creating a new bot instance...')
        Bot.instance = Bot()

    return Bot.instance


def load_all_modules_from_dir(dirname):
    log.debug('Loading modules from "%s"' % dirname)
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        log.debug("Importing '%s'" % package_name)
        importer.find_module(package_name).load_module(package_name)


class AlphaBotException(Exception):
    """Top of hierarchy for all alphabot failures."""

class CoreFailures(AlphaBotException):
    """Used to signify a failure in the robot's core."""

class Bot(object):

    instance=None

    def __init__(self):
        self.regex_commands = []
        self.engine = 'slack'

        if not SLACK_TOKEN:
            raise CoreFailures('SLACK_TOKEN required for slack engine.')

    @gen.coroutine
    def connect(self):
        log.info('Authenticating...')
        response = requests.get(SLACK_START + '?token=' + SLACK_TOKEN).json()
        log.info('Logged in!')

        self.socket_url = response['url']
        self.connection = yield websocket.websocket_connect(self.socket_url)

    @gen.coroutine
    def gather_scripts(self):
        script_paths = ['alphabot/scripts']
        for path in script_paths:
            load_all_modules_from_dir(path)

    @gen.coroutine
    def send(self, text, to):
        payload = json.dumps({
            "id": 1,
            "type": "message",
            "channel": to,
            "text": text
        })
        log.debug(payload)
        yield self.connection.write_message(payload)

    def get_chat(self, message):
        return Chat(bot=self, message=message)

    @gen.coroutine
    def start(self):

        while True:
            message = yield self.connection.read_message()

            if message is None:
                break

            message = json.loads(message)
            if not message.get('text'):
                continue

            log.info("Received: %s" % message)

            # New style of invoking scripts
            for pair in self.regex_commands:
                regex, function = pair
                match = re.match(regex, message.get('text'))
                if match:
                    log.debug('Command "%s" matches' % function.__name__)
                    chat = self.get_chat(message)
                    chat.regex_groups = match.groups()
                    try:
                        yield function(chat)
                    except:
                        chat.reply('Script %s had an error.' % function.__name__)
                        traceback.print_exc(file=sys.stdout)



    def add_command(self, regex):

        def decorator(function):
            log.info('New Command: "%s" => %s()' % (regex, function.__name__))
            self.regex_commands.append((regex, function))

        return decorator 


class Chat(object):

    def __init__(self, bot, message):
        self.bot = bot
        self.message = message

    @gen.coroutine
    def reply(self, text):
        """Reply to the original channel of the message."""
        yield self.bot.send(text, to=self.message.get('channel'))

    @gen.coroutine
    def react(self, reaction):
        client = httpclient.AsyncHTTPClient()
        yield client.fetch(
            (SLACK_REACT + 
            '?token=' + SLACK_TOKEN +
            '&name=' + reaction +
            '&timestamp=' + self.message.get('ts') + 
            '&channel=' + self.message.get('channel')))

