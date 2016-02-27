#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2014 Nextdoor.com, Inc

import logging
import argparse
import sys

from tornado import ioloop, gen
import requests

import alphabot.bot

requests.packages.urllib3.disable_warnings()

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)
logging.captureWarnings(True)
log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Alphabot')
parser.add_argument('-S', '--scripts', dest='scripts',
                    action='append', default=[],
                    help=('Direcotry or remote url to fetch bot scripts. '
                          'Can be specified multiple times'))

args = parser.parse_args()

def start_ioloop():
    try:
        ioloop.IOLoop.instance().run_sync(start_alphabot)
    except KeyboardInterrupt:
        pass
    except alphabot.bot.AlphaBotException as e:
        log.critical('Alphabot failed. Reason: %s' % e)

@gen.coroutine
def start_alphabot():

    # Add slack-specific adapter separater.
    bot = alphabot.bot.get_instance()

    yield [
            bot.connect(),
            bot.gather_scripts(args.scripts)
          ]
    yield bot.start()

if __name__ == '__main__':
    start_ioloop()
