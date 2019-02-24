#!/usr/bin/env python
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
import diceroller

log_file = 'service.log'


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
    
def send(bot, chat_id, msg):
    if msg == None or len(msg) == 0 or len(msg.split()) == 0:
        msg = '(no message)'
    bot.sendMessage(chat_id, msg)

def get_value_from(entry, value, default):
    if isinstance(value, list):
        for attempt in value:
            if attempt in entry:
                return entry[attempt]
    elif isinstance(value, str):
        if value in entry:
            return entry[value]
    return default

def newgame_already_started_usage():
    return """This game was already started in this group.
Now invite some players, make them join with `/player <character name>`, check your characters with `/show`, adjust your character sheet with `/update`, and roll dices with `/roll`.
For a more complete list of commands, see https://github.com/simonebaracchi/rpgbot."""

def start_in_private_msg_usage():
    return """Howdy, human.
I am a character sheet bot for Fate RPG.
To use my services, add me to a group, then start a new game with `/newgame <game name>`.
Other players can join with `/player <character name>`.
You can check your character with `/show`, adjust your character sheet with `/update`, and roll dices with `/roll`.
This is only a quick starter guide. For a more complete list of commands, see https://github.com/simonebaracchi/rpgbot.

Hope you have fun!"""

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

    log_msg(msg)
    dbc = db.open_connection()
    is_admin = False
    if sender_id in config.admins:
       is_admin = True

    args=text.split(maxsplit=1)
    command = args[0]
    if command == '/newgame':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        if len(args) < 2:
            send(bot, chat_id, 'Please specify the game name like this: `/newgame <name>`.')
            return
        if db.number_of_games(dbc, sender_id) > 10:
            send(bot, chat_id, 'You exceeded the maximum number of games. Please close some first.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        if gameid is not None:
            send(bot, chat_id, newgame_already_started_usage())
            return
        gameid = db.new_game(dbc, sender_id, username, args[1], chat_id, groupname, 'fae')
        if gameid is None:
            send(bot, chat_id, newgame_already_started_usage())
            return

        db.add_default_items(dbc, sender_id, gameid, 'fae')
        send(bot, chat_id, 'New game created: {}.'.format(args[1]))
    if command == '/delgame':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        if gameid is None:
            send(bot, chat_id, 'No game found.')
            return
        role = db.get_player_role(dbc, sender_id, gameid)
        if role != db.ROLE_MASTER:
            send(bot, chat_id, 'You need to be a game master to close a game.')
            return
        db.del_game(dbc, gameid)
        send(bot, chat_id, 'GG, humans.')
    if command == '/showgame':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        gamename, groups, players = db.get_game_info(dbc, gameid)
        players_string = [x + (' (gm)' if (y == db.ROLE_MASTER) else '') for x,y in players.items()]
        ret = '{}\nGroups: {}\nPlayers: {}'.format(gamename, ', '.join(groups), ', '.join(players_string))

        items = db.get_items(dbc, gameid, chat_id)
        if db.room_container in items:
            room_items = ['  - {}: {}\n'.format(key, items[db.room_container][key]) for key in sorted(items[db.room_container])]
            if len(room_items) > 0:
                ret += '\nRoom aspects:\n{}'.format('\n'.join(room_items))
        send(bot, chat_id, ret)

    if command == '/roll':
        if len(args) < 2:
            template = db.get_template_from_groupid(dbc, chat_id)
            if template == 'fae':
                dice = '4dF'
            else:
                # more templates here
                dice = '1d20'
        else:
            dice = args[1].strip()

        value = 0
        description = ''

        
        invalid_format = False
        try:
            value, description = diceroller.roll(dice)
        except (diceroller.InvalidFormat):
            invalid_format = True
        except (diceroller.TooManyDices):
            send(bot, chat_id, 'Sorry, try with less dices.')
            return

        if invalid_format:
            # Check saved rolls
            gameid = db.get_game_from_group(dbc, chat_id)
            saved_roll = db.get_item_value(dbc, gameid, sender_id, db.rolls_container, dice)
            if saved_roll is None:
                invalid_format = True
            else:
                invalid_format = False
                dice = saved_roll
                try:
                    value, description = diceroller.roll(dice)
                except (diceroller.InvalidFormat):
                    invalid_format = True
                except (diceroller.TooManyDices):
                    send(bot, chat_id, 'Sorry, try with less dices.')
                    return

        if invalid_format:
            send(bot, chat_id, 'Invalid dice format.')
            return

        send(bot, chat_id, 'Rolled {} = {}.'.format(description, value))

    if command == '/player':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        if len(args) < 2:
            send(bot, chat_id, 'Please specify the player name.')
            return
        if db.number_of_games(dbc, sender_id) > 10:
            send(bot, chat_id, 'You exceeded the maximum number of games. Please close some first.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        new_player_added = db.add_player(dbc, sender_id, args[1], gameid, db.ROLE_PLAYER)
        if new_player_added:
            template = db.get_template_from_gameid(dbc, gameid)
            db.add_default_items(dbc, sender_id, gameid, template)
            send(bot, chat_id, 'Welcome, {}.'.format(args[1]))
        else:
            send(bot, chat_id, 'You will now be known as {}.'.format(args[1]))

    if command == '/update' or command == '/add':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        if command == '/add' and db.number_of_items(dbc, gameid, sender_id) > 50:
            send(bot, chat_id, 'You exceeded the maximum number of items. Please delete some first.')
            return
        args = args[1].split(maxsplit=2)
        (container, key, change) = ('', '', '0')
        if len(args) == 2:
            (container, key) = args
            change = '+1'
        elif len(args) == 3:
            (container, key, change) = args
        else:
            send(bot, chat_id, 'Use the format: <container> <key> [change].')
            return
        owner = sender_id
        if container == db.room_container:
            owner = chat_id
        if command == '/update':
            replace_only = True
        else:
            replace_only = False
        oldvalue, newvalue = db.update_item(dbc, gameid, owner, container, key, change, replace_only)
        if newvalue is None:
            send(bot, chat_id, 'Item {}/{} not found.'.format(container, key))
        elif isinstance(oldvalue, int) and isinstance(newvalue, int):
            send(bot, chat_id, 'Updated {}/{} from {} to {} (changed {}).'.format(container, key, 
                 oldvalue, newvalue, newvalue-oldvalue))
        else:
            send(bot, chat_id, 'Updated {}/{} to "{}".'.format(container, key, newvalue))
    if command == '/addlist':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        if db.number_of_items(dbc, gameid, sender_id) > 50:
            send(bot, chat_id, 'You exceeded the maximum number of items. Please delete some first.')
            return
        args = args[1].split(maxsplit=1)
        if len(args) != 2:
            send(bot, chat_id, 'Use the format: <container> <description>.')
            return
        (container, description) = args
        owner = sender_id
        if container == db.room_container:
            owner = chat_id
        db.add_to_list(dbc, gameid, owner, container, description)
        send(bot, chat_id, 'Added "{}" to container {}.'.format(description, container))
    if command == '/del':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        args = args[1].split()
        if len(args) != 2:
            send(bot, chat_id, 'Use the format: <container> <key>.')
            return
        (container, key) = args
        owner = sender_id
        if container == db.room_container:
            owner = chat_id
        oldvalue = db.delete_item(dbc, gameid, owner, container, key)
        if oldvalue == None:
            send(bot, chat_id, 'Item {}/{} not found.'.format(container, key))
        else:
            send(bot, chat_id, 'Deleted {}/{} (was {}).'.format(container, key, oldvalue))

    if command == '/show':
        if not is_group:
            send(bot, chat_id, 'You must run this command in a group.')
            return
        gameid = db.get_game_from_group(dbc, chat_id)
        items = db.get_items(dbc, gameid, sender_id)
        playername = db.get_player_name(dbc, gameid, sender_id)
        if playername is None:
            send(bot, chat_id, 'You are not in a game.')
            return
        ret = ''
        ret += 'Character sheet for {}:\n'.format(playername)
        if items is None:
            send(bot, chat_id, 'No items found.')
            return
        for container in db.preferred_container_order:
            if container not in items:
                continue
            if container in db.preferred_key_order:
                keys = db.preferred_key_order[container]
            else:
                keys = []
            ret += container + ':\n'
            # print keys in preferred order
            for key in keys:
                if key not in items[container]:
                    continue
                ret += '  - {} ({})\n'.format(key, items[container][key])
                del items[container][key]
            # print remaining keys
            for key in sorted(items[container]):
                ret += '  - {} ({})\n'.format(key, items[container][key])
            del items[container]
            
        # print everything in remaining containers
        for container in items:
            ret += container + ':\n'
            for key in items[container]:
                ret += '  - {} ({})\n'.format(key, items[container][key])
        send(bot, chat_id, ret)

    if command == '/start':
        if is_group:
            return
        send(bot, chat_id, start_in_private_msg_usage())

    db.close_connection(dbc)

db.init()
bot = telepot.Bot(config.bot_token)
print('Entering message loop.')
bot.message_loop(process_message)

while 1:
    time.sleep(10)
