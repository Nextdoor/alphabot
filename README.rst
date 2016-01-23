Alpha Bot
---------
Open source python bot to chat with `Slack <https://slack.com/>`_ and, eventually, other platforms.

Inspired by `Hubot <https://hubot.github.com/>`_. Alphabot is written in `Tornado <http://www.tornadoweb.org/en/stable/>`_ combining the power of `Python <https://www.python.org/>`_ with the speed of coroutines.

Installation
============

.. code-block:: bash

    pip install alphabot


Running the bot
===============
Until this is packaged as a pip this is the way to start the bot:

.. code-block:: bash

    export SLACK_TOKEN=xoxb-YourToken
    python alphabot/app.py
