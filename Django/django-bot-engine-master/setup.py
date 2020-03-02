#!/usr/bin/env python

from setuptools import setup


setup(
    name='django-bot-engine',
    version='0.1.1',
    description='Django application for creating bots for different chat platforms.',
    url='https://github.com/terentjew-alexey/django-bot-engine',
    license='Apache 2.0',
    author='Aleksey Terentyev',
    author_email='terentjew.alexey@gmail.com',
    packages=['bot_engine', 'bot_engine.messengers'],
    install_requires=[
        'djangorestframework>=3.11,<4.0',
        'urllib3',
        'PySocks>=1.7',
        'requests>=2.22',
        'viberbot>=1.0.11',
        'pyTelegramBotAPI'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Environment :: Other Environment',
        'Operating System :: OS Independent',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries'
    ]
)
