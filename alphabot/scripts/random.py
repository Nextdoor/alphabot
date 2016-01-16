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
        #yield gen.sleep(3)
        yield message.react('burrito')

# Alternative syntax to consider implementing:
# bot.add_command('lunch', lunch_suggestion)
