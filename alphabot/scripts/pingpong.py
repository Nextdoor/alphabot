from tornado import gen

@gen.coroutine
def hear(text, chat):
    if text == 'ping':
        yield chat.reply('pong')
