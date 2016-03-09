from tornado import gen

import alphabot.bot

# Actual bot instance. Will be available because this file should only be
# invoked inside of a script-discovery code of the bot itself!
bot = alphabot.bot.get_instance()

@bot.add_command('lunch')
@gen.coroutine
def lunch_suggestion(message):

    yield message.reply("How about Chipotle?")

    if bot.engine == 'slack':
        yield message.react('burrito')

@bot.add_command('hi')
@gen.coroutine
def conversation(message):

    yield message.reply("How are you?")

    response = yield message.wait_for_regex('(.*)')

    yield message.reply("%s? Me too!" % response.message['text'])
