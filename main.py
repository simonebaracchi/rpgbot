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
from telepot.loop import MessageLoop
from telepot.delegate import pave_event_space, per_chat_id, create_open, flavor, include_callback_query_chat_id, per_callback_query_origin, per_callback_query_chat_id

import config
import db
import commands
import keyboard

os.chdir(os.path.dirname(os.path.abspath(__file__)))

db.init()
#bot = telepot.Bot(config.bot_token)
print('Entering message loop.')
#bot.message_loop(process_message)

bot = telepot.DelegatorBot(config.bot_token, [
    pave_event_space()(
        [per_chat_id(), per_callback_query_chat_id()], create_open, keyboard.MessageHandler, timeout=300, include_callback_query=True),
])
MessageLoop(bot).run_as_thread()

while 1:
    time.sleep(10)


