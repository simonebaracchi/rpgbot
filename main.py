#!/usr/bin/env python3
# Telegram RPG Character Sheet bot

from pprint import pprint
import telepot
import time
import socket
import os
import re
import sys
import json

import config
import db
import commands

log_file = 'service.log'
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Operation:
    def __init__(self, id, type, name):
        self.id = id
        self.type = type
        self.name = name
    def __eq__(self, other):
        return self.id == other.id

def die():
    os.kill(os.getpid(), signal.SIGINT)

def fatal(msg):
    print(msg)
    die()

def log(msg):
    f = open(log_file, 'a')
    f.write(msg + "\n")
    f.close()
    print(msg)

def log_msg(msg):
    chat_name = ''
    username = get_value_from(msg['from'], ['username', 'first_name', 'id'], 'unknown-user-id')
    text = msg['text']
    if 'title' in msg['chat']:
        chat_name = '{} ({})'.format(msg['chat']['title'], username)
    else:
        chat_name = username
    log('{}: {}'.format(chat_name, text))
    
def get_value_from(entry, value, default):
    if isinstance(value, list):
        for attempt in value:
            if attempt in entry:
                return entry[attempt]
    elif isinstance(value, str):
        if value in entry:
            return entry[value]
    return default

def process_message(msg):
    """
    Process received messages.

    msg -- The received message
    """
    if 'text' not in msg:
        # probably a sticker or something
        return
    text = msg['text']
    chat_id = msg['chat']['id']
    sender_id = msg['from']['id']
    username = get_value_from(msg['from'], ['username', 'first_name', 'id'], 'unknown-user-id')
    is_group = msg['chat']['type'] == 'group'
    groupname = msg['chat']['title'] if 'title' in msg['chat'] else None

    # avoid logging and processing every single message.
    if text[0] != '/':
        return
    # get command, ignore bot username
    args=text.split()
    command = args[0]
    if '@' in command:
        more_split = command.split('@', maxsplit=1)
        command = more_split[0]
    # skip '/'
    command = command[1:]

    log_msg(msg)
    dbc = db.open_connection()
    is_admin = False
    if sender_id in config.admins:
       is_admin = True

    cmd_params = {
        'bot': bot,
        'dbc': dbc,
        'chat_id': chat_id,
        'sender_id': sender_id,
        'username': username,
        'groupname': groupname,
        'input_args': args,
        'is_group': is_group,
        'command': command
        }

    if command in commands.all_commands:
        return commands.all_commands[command](**cmd_params)

    db.close_connection(dbc)

db.init()
bot = telepot.Bot(config.bot_token)
print('Entering message loop.')
bot.message_loop(process_message)

while 1:
    time.sleep(10)
