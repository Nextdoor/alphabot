import logging
import random

from tornado import gen

import alphabot.bot

# Actual bot instance. Will be available because this file should only be
# invoked inside of a script-discovery code of the bot itself!
bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)


@bot.on_schedule(minute='0')
@gen.coroutine
def still_here():
    channel = bot.get_channel(name='alphabot-debug')
    if channel:
        yield channel.send('I am still here!')


@bot.add_command('button-example')
@gen.coroutine
def button_example(message):

    action = yield message.button_prompt(
        'Is this a good button example?',
        ['No', 'Yes'])

    yield message.reply('Got "%s" from the button.' % action)


@bot.on(type='message', message='acknowledge')
@gen.coroutine
def acknowledge(event):
    message = bot.event_to_chat(event)
    yield message.reply('Tadaa!')
    log.info('Attached to a message!')


@bot.add_command('lunch')
@gen.coroutine
def lunch_suggestion(message):

    yield message.reply("How about Chipotle?")

    if bot.engine == 'slack':
        yield message.react('burrito')


@bot.add_command('hi')
@gen.coroutine
def conversation(message):

    log.info('Starting a conversation')
    yield message.reply("How are you?")

    response = yield message.listen_for('(.*)')

    yield message.reply("%s? Me too!" % response.text)


@bot.add_command('random number')
@gen.coroutine
def random_number(message):

    last_r = yield bot.memory.get('random_number')
    r = random.randint(1, 10)
    yield bot.memory.save('random_number', r)

    yield message.reply("Random number is %s" % r)
    if last_r is not None:
        yield gen.sleep(1)
        yield message.reply("But last time I said it was %s" % last_r)
