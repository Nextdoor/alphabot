import os
from setuptools import setup, find_packages

DIR = os.path.dirname(os.path.realpath(__file__))

setup(
    name = "alphabot",
    version = "0.0.0",
    author = "Mikhail Simin",
    author_email = "mikhail.simin@gmail.com",
    description = ("Bot that connects to Slack."),
    license = "Apache License, Version 2.0",
    keywords = "slack, chat, irc, hubot",
    url = "https://github.com/Nextdoor/alphabot",
    packages=find_packages(),
    long_description=open('%s/README.rst' % DIR).read(),
    install_requires=open('%s/requirements.txt' % DIR).readlines(),
    entry_points={
        'console_scripts': [
            'alphabot = alphabot.app:start_ioloop'
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Software Development',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: POSIX',
        'Natural Language :: English',
    ],
)
