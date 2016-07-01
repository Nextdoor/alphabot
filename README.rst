
Alpha Bot
---------
|pypi_download|_

.. image:: logo.png
    :align: left

Open source python bot to chat with `Slack <https://slack.com/>`_ and, eventually, other platforms.

Inspired by `Hubot <https://hubot.github.com/>`_. Alphabot is written in `Tornado <http://www.tornadoweb.org/en/stable/>`_ combining the power of `Python <https://www.python.org/>`_ with the speed of coroutines.

Installation
============

Raw:

.. code-block:: bash

    git clone https://github.com/Nextdoor/alphabot.git
    cd alphabot
    pip install -e .
    
Docker:

.. code-block:: bash

    docker run nextdoor/alphabot

Running the bot
===============

If you installed alphabot as a python package then simply run it:

.. code-block:: bash

    alphabot -S alphabot/sample-scripts/  # or...
    alphabot -S path/to/your/scripts/

.. code-block:: bash

    export SLACK_TOKEN=xoxb-YourToken
    alphabot --engine slack -S path/to your/scripts/


.. |pypi_download| image:: https://badge.fury.io/py/alphabot.png
.. _pypi_download: https://pypi.python.org/pypi/alphabot
