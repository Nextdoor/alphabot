import json
import logging
import os
import pkgutil
import re
import sys
import traceback

from tornado import websocket, gen, httpclient
from tornado.concurrent import Future
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


def handle_callback(future, chat):
    """Attach to Futures that are not yielded."""

    if not hasattr(future, 'add_done_callback'):
        log.error('Could not attach callback. Exceptions will be missed.')
        return

    def cb(future):
        """Custom callback which is chat aware."""
        try:
            future.result()
        except:
            chat.reply('Script %s had an error.' % function.__name__)
            traceback.print_exc(file=sys.stdout)

    # Tornado functionality to add a custom callback
    future.add_done_callback(cb)


class AlphaBotException(Exception):
    """Top of hierarchy for all alphabot failures."""

class CoreFailures(AlphaBotException):
    """Used to signify a failure in the robot's core."""

class Bot(object):

    instance=None

    def __init__(self):
        self.regex_commands = []
        self.engine = 'slack'
        self.chat_listeners = []

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
    def gather_scripts(self, script_paths=[]):
        log.info('Gathering scripts...')
        for path in script_paths:
            log.info('Gathering functions from %s' % path)
            load_all_modules_from_dir(path)
        if not script_paths:
            log.warning('Warning! You did not specify any scripts to load.')

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

            log.debug("Received: %s" % message)

            # New style of invoking scripts
            for pair in self.regex_commands:
                regex, function = pair
                match = re.match(regex, message.get('text'))
                if match:
                    log.info('Command "%s" matches' % function.__name__)
                    chat = self.get_chat(message)
                    chat.regex_groups = match.groups()
                    future = function(chat)
                    if type(future) != Future:
                        log.error('Function "%s" is not a Tornado Future' % function.__name__)
                    handle_callback(future, chat)

            for chat in self.chat_listeners:
                chat.hear(message)

    def add_listener(self, chat):
        self.chat_listeners.append(chat)

    def remove_listener(self, chat):
        self.chat_listeners.remove(chat)

    def add_command(self, regex, direct=False):

        def decorator(function):
            log.info('New Command: "%s" => %s()' % (regex, function.__name__))
            self.regex_commands.append((regex, function))

        return decorator 


class Chat(object):

    def __init__(self, bot, message):
        self.bot = bot
        self.message = message
        self.listening = False

    @gen.coroutine
    def reply(self, text):
        """Reply to the original channel of the message."""
        log.debug('Sending a reply...')
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

    #TODO: Add a timeout here. Don't want to hang forever.
    @gen.coroutine
    def wait_for_regex(self, regex):
        self.bot.add_listener(self)
        self.listening = regex

        # Hang until self.hear() sets this to False
        while self.listening:
            yield gen.moment

        self.bot.remove_listener(self)

        raise gen.Return(self.heard_message)

    @gen.coroutine
    def hear(self, new_message):
        """Invoked by the Bot class to note that `message` was heard."""
        log.info('Just heard %s' % new_message)
        if new_message.get('user') != self.message['user']:
            log.info('Heard this from a wrong user.')
            return

        if new_message.get('ts') == self.message.get('ts'):
            log.info('Messages have same timestamp ID. Skipping.');
            return

        log.info('Message %s is from the correct user!' % new_message['text'])

        match = re.match(self.listening, new_message['text'])
        log.info('Match is %s' % match)
        if match:
            log.info('It matches!')
            self.listening = False
            # Generate full-blown chat object here.
            self.heard_message = self.bot.get_chat(new_message)
            raise gen.Return()

        log.info('It does not match %s' % self.listening)
