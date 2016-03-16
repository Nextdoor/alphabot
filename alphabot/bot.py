import copy
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

from alphabot import memory

log = logging.getLogger(__name__)


class AlphaBotException(Exception):
    """Top of hierarchy for all alphabot failures."""

class CoreException(AlphaBotException):
    """Used to signify a failure in the robot's core."""

class InvalidOptions(AlphaBotException):
    """Robot failed because input options were somehow broken."""

def get_instance(engine='cli'):
    if not Bot.instance:
        engine_map = {
            'cli': Bot_CLI,
            'slack': Bot_Slack
        }
        if not engine_map.get(engine):
            raise InvalidOptions('Bot engine "%s" is not available.' % engine)

        log.debug('Creating a new bot instance. engine: %s' % engine)
        Bot.instance = engine_map.get(engine)()

    return Bot.instance


def load_all_modules_from_dir(dirname):
    log.debug('Loading modules from "%s"' % dirname)
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        log.debug("Importing '%s'" % package_name)
        importer.find_module(package_name).load_module(package_name)


def handle_exceptions(future, chat):
    """Attach to Futures that are not yielded."""

    if not hasattr(future, 'add_done_callback'):
        log.error('Could not attach callback. Exceptions will be missed.')
        return

    def cb(future):
        """Custom callback which is chat aware."""
        try:
            future.result()
        except:
            chat.reply('Script had an error.')
            # FIXME: send to log, not stdout
            traceback.print_exc(file=sys.stdout)

    # Tornado functionality to add a custom callback
    future.add_done_callback(cb)


class Bot(object):

    instance=None

    def __init__(self):
        self.regex_commands = []
        self.chat_listeners = []
        self.memory = None

    @gen.coroutine
    def setup(self, memory_type, script_paths):
        yield self._setup_memory(memory_type=memory_type)
        yield self._setup()  # Engine specific setup
        yield self._gather_scripts(script_paths)

    @gen.coroutine
    def _setup_memory(self, memory_type='dict'):

        memory_map = {
            'dict': memory.Memory_Dict,
        }

        # Get assiciated memory class or default to Dict memory type.
        NewMemory = memory_map.get(memory_type, memory.Memory_Dict)
        self.memory = NewMemory()
        yield self.memory.setup()

    @gen.coroutine
    def _gather_scripts(self, script_paths=[]):
        log.info('Gathering scripts...')
        for path in script_paths:
            log.info('Gathering functions from %s' % path)
            load_all_modules_from_dir(path)
        if not script_paths:
            log.warning('Warning! You did not specify any scripts to load.')

    @gen.coroutine
    def start(self):

        log.debug('Bot started! Listening to messages.')
        while True:
            next_message = yield self._next_message()

            for chat in self.chat_listeners:
                message = copy.copy(next_message)
                future = chat.hear(message)
                handle_exceptions(future, message)

            for regex, function in self.regex_commands:
                message = copy.copy(next_message)
                if not message.matches_regex(regex):
                    continue

                # Execute the matching script function
                # We do not call yield here because this command may wait for
                # future messages, and we cannot "block" here.
                log.debug('Invoking function %s' % function.__name__)
                future = function(message)
                handle_exceptions(future, message)

    @gen.coroutine
    def _next_message(self):
        raise CoreException('Chat engine "%s" is missing _next_message' % (
            self.__class__.__name__))

    def add_listener(self, chat):
        self.chat_listeners.append(chat)

    def remove_listener(self, chat):
        self.chat_listeners.remove(chat)

    def add_command(self, regex, direct=False):

        def decorator(function):
            log.info('New Command: "%s" => %s()' % (regex, function.__name__))
            self.regex_commands.append((regex, function))

        return decorator 

class Bot_CLI(Bot):

    @gen.coroutine
    def _setup(self):
        pass


class Bot_Slack(Bot):

    api_start = 'https://slack.com/api/rtm.start'
    api_react = 'https://slack.com/api/reactions.add'

    @gen.coroutine
    def _setup(self):
        self._token = os.getenv('SLACK_TOKEN')
        if not self._token:
            raise InvalidOptions('SLACK_TOKEN required for slack engine.')

        log.info('Authenticating...')
        response = requests.get(self.api_start + '?token=' + self._token).json()
        log.info('Logged in!')

        self.socket_url = response['url']
        self.connection = yield websocket.websocket_connect(self.socket_url)

    def _slack_to_chat(self, message):
        return Chat(text=message.get('text'),
                    user=message.get('user'),
                    channel=message.get('channel'),
                    raw=message,
                    bot=self)

    @gen.coroutine
    def _next_message(self):
        """Fetch the next message and construct return a Chat object."""
        msg = yield self._read_message()
        message = self._slack_to_chat(msg)

        raise gen.Return(message)

    @gen.coroutine
    def _read_message(self):
        """Slack-specific message reader."""
        while True:
            message = yield self.connection.read_message()
            log.debug(message)

            message = json.loads(message)
            if message.get('type') != 'message':
                continue
            else:
                break

        raise gen.Return(message)

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


class Chat(object):
    """Wrapper for Message, Bot and helpful functions.
    
    This gets passed to the receiving script's function.
    """

    def __init__(self, text, user, channel, raw, bot):
        self.text = text
        self.user = user  # TODO: Create a User() object
        self.channel = channel  # TODO: Create a Channel() object
        self.bot = bot
        self.raw = raw
        self.listening = False
        self.regex_groups = None

    def matches_regex(self, regex):
        """Check if this message matches the regex.
        
        If it does store the groups for later use.
        """
        match = re.match(regex, self.text)
        if not match:
            return False

        self.regex_groups = match.groups()
        return True

    @gen.coroutine
    def reply(self, text):
        """Reply to the original channel of the message."""
        log.debug('Sending a reply...')
        yield self.bot.send(text, to=self.channel)

    # TODO: figure out how to make this Slack-specific
    @gen.coroutine
    def react(self, reaction):
        client = httpclient.AsyncHTTPClient()
        yield client.fetch(
            (self.api_react+ 
            '?token=' + self._token +
            '&name=' + reaction +
            '&timestamp=' + self.message.get('ts') + 
            '&channel=' + self.message.get('channel')))

    #TODO: Add a timeout here. Don't want to hang forever.
    @gen.coroutine
    def listen_for(self, regex):
        self.listening = regex

        # Hang until self.hear() sets this to False
        self.bot.add_listener(self)
        while self.listening:
            yield gen.moment
        self.bot.remove_listener(self)

        raise gen.Return(self.heard_message)

    @gen.coroutine
    def hear(self, new_message):
        """Invoked by the Bot class to note that `message` was heard."""

        # TODO: some flag should control this filter
        if new_message.user != self.user:
            log.debug('Heard this from a wrong user.')
            return

        match = re.match(self.listening, new_message.text)
        log.info('Match is %s' % match)
        if match:
            log.info('It matches!')
            self.listening = False
            self.heard_message = new_message
            raise gen.Return()

        log.info('It does not match %s' % self.listening)
