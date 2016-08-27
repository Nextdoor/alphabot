import logging

from tornado import gen

import alphabot.bot

bot = alphabot.bot.get_instance()
log = logging.getLogger(__name__)


@bot.add_command('!help$')
@bot.add_help('Get help for commands', usage='!help')
@gen.coroutine
def help(message):
    help_text = _make_help_text(bot.help.list())
    yield message.reply(help_text)


@bot.add_command('!help (.*)')
@bot.add_help('Get help for commands', usage='!help <query>')
@gen.coroutine
def help_query(message):
    query = message.regex_groups[0]
    help_text = _make_help_text(bot.help.list(query))
    yield message.reply(help_text)


def _make_help_text(help_list):
    reply = ''
    for usage, desc in help_list:
        if desc:
            reply += '`%s` - %s\n' % (usage, desc)
        else:
            reply += '`%s`\n' % usage
    return reply
