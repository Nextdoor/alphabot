Alpha bot
---------
Open source python bot to chat with Slack and, eventually, other platforms.

Inspired by `Hubot <https://hubot.github.com/>`_. Alphabot is written in Tornado combining the power of Python with the speed of coroutines.

Installation
============

.. code-block:: bash

    virtualenv .venv
    make build


Running the bot
===============
Until this is packaged as a pip this is the way to start the bot:

.. code-block:: bash

    export PYTHONPATH=$(pwd)
    export SLACK_TOKEN=xoxb-YourToken
    python alphabot/app.py
