import sys
import time
import telepot
from pprint import pprint
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import config
import commands
import db

class CallbackRequest():
    def __init__(self, callback, argname, kwargs):
        self.callback = callback
        self.argname = argname
        self.kwargs = kwargs

class MessageHandler(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        self.sender_id = None
        self.username = None
        self.is_group = None
        self.groupname = None
        self.command = None
        self.args = None
        self.message = None
        self.player = None # not automatically initialized
        self.group = None # not automatically initialized
        self.callback = None # string to be read requested

    def on_chat_message(self, msg):
        """
        Process received messages.

        msg -- The received message
        """
        if 'text' not in msg:
            # probably a sticker or something
            return

        if self.callback and self.sender_id != msg['from']['id']:
            # once in callback mode, ignore everyone else
            return
    
        text = msg['text']
        #self.chat_id = msg['chat']['id']
        self.sender_id = msg['from']['id']
        self.username = get_value_from(msg['from'], ['username', 'first_name', 'id'], 'unknown-user-id')
        self.is_group = msg['chat']['type'] == 'group'
        self.groupname = msg['chat']['title'] if 'title' in msg['chat'] else None
        #log('chat id {} from {}: {}'.format(self.chat_id, self.sender_id, str(msg)))

        if self.callback:
            log_msg(msg)
            callback = self.callback
            self.callback = None
            callback.kwargs[callback.argname] = text
            self.dbc = db.open_connection()
            callback.callback(self, **callback.kwargs)
            db.close_connection(self.dbc)
            return

        # avoid logging and processing every single message.
        if text[0] != '/':
            return
        # get command, ignore bot username
        self.args=text.split()
        command = self.args[0]
        if '@' in command:
            more_split = command.split('@', maxsplit=1)
            command = more_split[0]
        # skip '/'
        self.command = command[1:]

        log_msg(msg)

        #is_admin = False
        #if sender_id in config.admins:
        #   is_admin = True

        if self.command in commands.all_commands:
            self.dbc = db.open_connection()
            commands.all_commands[self.command](self)
            db.close_connection(self.dbc)

    def read_answer(self, callback, argname, kwargs):
        self.callback = CallbackRequest(callback, argname, kwargs)
        
    def burn_message(self, msg_id):
        # destroy the inline keyboard
        #self.bot.deleteMessage((self.chat_id, msg['message']['message_id']))
        self.bot.editMessageText(msg_id, 'Too late.')
        pass

    def send(self, msg, target=None, disablepreview=True, options={}, allowedit=False):
        if (msg == None or len(msg) == 0 or len(msg.split()) == 0) and len(options) == 0:
            msg = '(no message)'

        keyboard = None
        if len(options) > 0:
            buttons = []
            for key, value in options.items():
                if isinstance(value, dict):
                    if 'url' in value:
                        buttons.append([InlineKeyboardButton(text=key, url=value['url'])])
                    else:
                        sublist = []
                        for key, subvalue in value.items():
                            sublist.append(InlineKeyboardButton(text=key, callback_data=subvalue))
                        buttons.append(sublist)
                else:
                    buttons.append([InlineKeyboardButton(text=key, callback_data=value)])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        #log('sending to chat id {}'.format(target))
        if target is None:
            if self.message is not None:
                self.bot.deleteMessage(self.message)
            sent = self.bot.sendMessage(self.chat_id, msg, disable_web_page_preview=disablepreview, reply_markup=keyboard)
            if allowedit:
                self.message = telepot.message_identifier(sent)
            else:
                self.message = None
        else:
            self.bot.sendMessage(target, msg, disable_web_page_preview=disablepreview, reply_markup=keyboard)

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        #self.bot.sendMessage(from_id, str(msg))
        #log('callback chat id {} from {}: {}'.format(self.chat_id, from_id, str(msg)))

        if self.callback and self.sender_id != from_id:
            # once in callback mode, ignore everyone else
            return

        if self.message is None:
            # probably bot restarted
            self.message = (self.chat_id, msg['message']['message_id'])
    
        log_callback(msg, self.callback)

        if self.callback:
            callback = self.callback
            self.callback = None
            callback.kwargs[callback.argname] = query_data
            self.dbc = db.open_connection()
            callback.callback(self, **callback.kwargs)
            db.close_connection(self.dbc)
            return
        if query_data in commands.all_commands:
            self.command = query_data
            self.dbc = db.open_connection()
            commands.all_commands[query_data](self)
            db.close_connection(self.dbc)
            return
        #bot.answerCallbackQuery(query_id) #, text='Got it')
        # Destroy message if we can't understand what it is. Probably an old message.
        self.burn_message(self.message)

    def on_close(self, ex):
        try:
            self.burn_message(self.message)
        except:
            pass

def die():
    os.kill(os.getpid(), signal.SIGINT)

def fatal(msg):
    print(msg)
    die()

def log(msg):
    f = open(config.log_file, 'a')
    f.write(msg + "\n")
    f.close()
    print(msg)

def log_callback(msg, callback):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    chat_name = ''
    username = get_value_from(msg['from'], ['username', 'first_name', 'id'], 'unknown-user-id')
    log('{}: callback {}: {}'.format(username, callback.argname if callback is not None else '(none)', query_data))

def log_msg(msg):
    chat_name = ''
    username = ''
    username = get_value_from(msg['from'], ['username', 'first_name'], 'unknown-user-id')
    username = '{}[{}]'.format(username, msg['from']['id'])
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


