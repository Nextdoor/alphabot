Alpha Bot
---------
|pypi_download|_

Open source python bot to chat with `Slack <https://slack.com/>`_ and, eventually, other platforms.

Inspired by `Hubot <https://hubot.github.com/>`_. Alphabot is written in `Tornado <http://www.tornadoweb.org/en/stable/>`_ combining the power of `Python <https://www.python.org/>`_ with the speed of coroutines.

Installation
============

Python:

.. code-block:: bash

    pip install alphabot

Docker:

.. code-block:: bash

    docker run nextdoor/alphabot

Running the bot
===============

If you installed alphabot as a python package then simply run it:

.. code-block:: bash

    export SLACK_TOKEN=xoxb-YourToken
    alphabot


.. |pypi_download| image:: https://badge.fury.io/py/alphabot.png
.. _pypi_download: https://pypi.python.org/pypi/alphabot
