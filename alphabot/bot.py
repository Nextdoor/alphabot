from __future__ import print_function

import copy
import json
import logging
import os
import pkgutil
import re
import sys
import traceback

from tornado import websocket, gen, httpclient, ioloop
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
            'cli': BotCLI,
            'slack': BotSlack
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
            log.error('Script had an error', exc_info=1)
            chat.reply('Script had an error.')

    # Tornado functionality to add a custom callback
    future.add_done_callback(cb)


class Bot(object):

    instance = None

    def __init__(self):
        self.event_listeners = []
        self.memory = None

    @gen.coroutine
    def setup(self, memory_type, script_paths):
        yield self._setup_memory(memory_type=memory_type)
        yield self._setup()  # Engine specific setup
        yield self._gather_scripts(script_paths)

    @gen.coroutine
    def _setup_memory(self, memory_type='dict'):

        # TODO: memory module should provide this mapping.
        memory_map = {
            'dict': memory.MemoryDict,
            'redis': memory.MemoryRedis,
        }

        # Get associated memory class or default to Dict memory type.
        MemoryClass = memory_map.get(memory_type)
        if not MemoryClass:
            raise InvalidOptions(
                'Memory type "%s" is not available.' % memory_type)

        self.memory = MemoryClass()
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

        log.info('Bot started! Listening to events.')

        while True:
            event = yield self._get_next_event()
            log.debug('Received event: %s' % event)
            log.debug('Checking against %s listeners' % len(self.event_listeners))

            # Note: Copying the event_listeners list here to prevent
            # mid-loop modification of the list.
            for kwargs, function in list(self.event_listeners):
                log.debug('Checking "%s"' % function.__name__)
                match = self.check_event_kwargs(event, kwargs)
                if match:
                    future = function(event=event)
                    handle_exceptions(future, event)
                yield gen.moment

    @gen.coroutine
    def _next_message(self):
        raise CoreException('Chat engine "%s" is missing _next_message()' % (
            self.__class__.__name__))

    @gen.coroutine
    def send(self, text, to):
        raise CoreException('Chat engine "%s" is missing send(...)' % (
            self.__class__.__name__))

    def add_listener(self, chat):
        log.info('Adding chat listener...')
        @gen.coroutine
        def cmd(event):
            message = self.event_to_chat(event)
            chat.hear(message)

        # Uniquely identify this `cmd` to delete later.
        cmd._listener_chat_id = id(chat)

        self.on(type='message')(cmd)

    def remove_listener(self, chat):
        match = None
        # Have to search all the event_listeners here
        for kw, function in self.event_listeners:
            if (hasattr(function, '_listener_chat_id') and
                    function._listener_chat_id == id(chat)):
                match = (kw, function)
        self.event_listeners.remove(match)

    def on(self, **kwargs):
        def decorator(function):
            log.info('New Listener: %s => %s()' % (kwargs, function.__name__))
            self.event_listeners.append((kwargs, function))

        return decorator

    def add_command(self, regex, direct=False):
        def decorator(function):
            log.info('New Command: %s' % function.__name__)

            @gen.coroutine
            def cmd(event):
                message = self.event_to_chat(event)
                if not message.matches_regex(regex):
                    return
                function(message)
            cmd.__name__ = function.__name__

            self.on(type='message')(cmd)

        return decorator 

    def check_event_kwargs(self, event, kwargs):
        """Check that all expected kwargs were satisfied by the event."""
        return kwargs.items() <= event.items()


class BotCLI(Bot):

    @gen.coroutine
    def _setup(self):
        self.print_prompt()
        ioloop.IOLoop.instance().add_handler(
            sys.stdin, self.capture_input, ioloop.IOLoop.READ)

        self.input_line = None

    def print_prompt(self):
        print('\033[4mAlphabot\033[0m> ', end='')

    def capture_input(self, fd, events):
        self.input_line = fd.readline().strip()
        if self.input_line is None or self.input_line == '':
            self.input_line = None
        self.print_prompt()

    @gen.coroutine
    def _get_next_event(self):
        while not self.input_line:
            yield gen.moment

        user_input = self.input_line
        self.input_line = None

        event = { 'type': 'message',
                  'message': user_input }

        raise gen.Return(event)

    def event_to_chat(self, event):
        return Chat(
            text=event['message'],
            user='User',
            channel='CLI',
            raw=event['message'],
            bot=self)

    @gen.coroutine
    def _next_message(self):
        while not self.input_line:
            yield gen.moment

        user_input = self.input_line
        self.input_line = None

        chat = Chat(
            text=user_input,
            user='User',
            channel='CLI',
            raw=user_input,
            bot=self)

        raise gen.Return(chat)

    @gen.coroutine
    def send(self, text, to):
        print(text)


class BotSlack(Bot):

    engine = 'slack'

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

    def event_to_chat(self, message):
        return Chat(text=message.get('text'),
                    user=message.get('user'),
                    channel=message.get('channel'),
                    raw=message,
                    bot=self)

    @gen.coroutine
    def _get_next_event(self):
        """Slack-specific message reader."""
        message = yield self.connection.read_message()
        log.debug(message)

        message = json.loads(message)
        #if message.get('type') != 'message':
        #    continue
        #else:
        #    break

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
        yield self.bot.send(text, to=self.channel)

    # TODO: figure out how to make this Slack-specific
    @gen.coroutine
    def react(self, reaction):
        client = httpclient.AsyncHTTPClient()
        yield client.fetch(
            (self.bot.api_react+
             '?token=' + self.bot._token +
             '&name=' + reaction +
             '&timestamp=' + self.raw.get('ts') +
             '&channel=' + self.channel))

    # TODO: Add a timeout here. Don't want to hang forever.
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
