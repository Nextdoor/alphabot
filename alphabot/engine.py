#from alphabot import bot

# Decorators for registering bot commands
def listen(regex):

    print 'listen: %s' % regex 
    def wrapper(function):
        print 'got a function: %s' % function
        def decorator(*args, **kwargs):
            return function(*args, **kwargs)
        return decorator

    print 'returning decorator'
    return wrapper
