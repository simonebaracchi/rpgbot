import telepot
import functools
import db
import diceroller

all_commands = {}

def newgame_already_started_usage():
    return """This game was already started in this group.
Now invite some players, make them join with `/player <character name>`, check your characters with `/show`, adjust your character sheet with `/update`, and roll dices with `/roll`.
For a more complete list of commands, see https://github.com/simonebaracchi/rpgbot."""

def start_usage():
    return """Howdy, human.
I am a character sheet bot for Fate RPG.
To use my services, add me to a group, then start a new game with `/newgame <game name>`.
Other players can join with `/player <character name>`.
You can check your character with `/show`, adjust your character sheet with `/update`, and roll dices with `/roll`.
This is only a quick starter guide. For a more complete list of commands, see https://github.com/simonebaracchi/rpgbot.

Hope you have fun!"""

def send(bot, chat_id, msg, disablepreview=True):
    if msg == None or len(msg) == 0 or len(msg.split()) == 0:
        msg = '(no message)'
    bot.sendMessage(chat_id, msg, disable_web_page_preview=disablepreview)

def add_command(name):
    global all_commands
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        all_commands[name] = func
        return wrapper 
    return decorator

def need_args(number, errormessage):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, bot, chat_id, input_args, **kwargs):
            if len(input_args) < 1 + number:
                send(bot, chat_id, errormessage)
                return False
            return func(*args, bot=bot, chat_id=chat_id, input_args=input_args, **kwargs)
        return wrapper 
    return decorator

def need_group(func):
    @functools.wraps(func)
    def wrapper(*args, bot, chat_id, is_group, **kwargs):
        if is_group is not True:
            send(bot, chat_id, 'You must run this command in a group.')
            return False
        return func(*args, bot=bot, chat_id=chat_id, is_group=is_group, **kwargs)
    return wrapper 

def check_too_many_games(func):
    @functools.wraps(func)
    def wrapper(*args, dbc, bot, chat_id, sender_id, **kwargs):
        if db.number_of_games(dbc, sender_id) > 10:
            send(bot, chat_id, 'You exceeded the maximum number of games. Please close some first.')
            return False
        return func(*args, dbc=dbc, bot=bot, chat_id=chat_id, sender_id=sender_id, **kwargs)
    return wrapper 

def need_gameid(mustbenone, errormessage=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, bot, dbc, chat_id, **kwargs):
            gameid = db.get_game_from_group(dbc, chat_id)
            if mustbenone is True and gameid is not None or mustbenone is False and gameid is None:
                send(bot, chat_id, errormessage)
                return False
            return func(*args, bot=bot, dbc=dbc, gameid=gameid, chat_id=chat_id, **kwargs)
        return wrapper 
    return decorator 

def need_role(role, errormessage):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, bot, dbc, sender_id, gameid, chat_id, **kwargs):
            user_role = db.get_player_role(dbc, sender_id, gameid)
            if user_role != role:
                send(bot, chat_id, errormessage)
                return False
            return func(*args, bot=bot, dbc=dbc, gameid=gameid, sender_id=sender_id, chat_id=chat_id, **kwargs)
        return wrapper 
    return decorator 


@add_command('newgame')
@need_group
@need_gameid(mustbenone=True, errormessage=newgame_already_started_usage())
@need_args(1, 'Please specify the game name like this: `/newgame <name>`.')
@check_too_many_games
def newgame(bot, dbc, chat_id, sender_id, username, groupname, input_args, *args, **kwargs):
    if db.number_of_games(dbc, sender_id) > 10:
        send(bot, chat_id, 'You exceeded the maximum number of games. Please close some first.')
        return False
    gamename = ' '.join(input_args[1:])
    gameid = db.new_game(dbc, sender_id, username, gamename, chat_id, groupname, 'fae')
    if gameid is None:
        send(bot, chat_id, newgame_already_started_usage())
        return False

    db.add_default_items(dbc, sender_id, gameid, 'fae')
    send(bot, chat_id, 'New game created: {}.'.format(gamename))


@add_command('delgame')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_role(db.ROLE_MASTER, 'You need to be a game master to close a game.')
def delgame(bot, dbc, chat_id, gameid, *args, **kwargs):
    db.del_game(dbc, gameid)
    send(bot, chat_id, 'GG, humans.')

@add_command('showgame')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
def showgame(bot, dbc, gameid, chat_id, *args, **kwargs):
    gamename, groups, players = db.get_game_info(dbc, gameid)
    players_string = [x + (' (gm)' if (y == db.ROLE_MASTER) else '') for x,y in players.items()]
    ret = '{}\nGroups: {}\nPlayers: {}'.format(gamename, ', '.join(groups), ', '.join(players_string))

    items = db.get_items(dbc, gameid, chat_id)
    if db.room_container in items:
        room_items = ['  - {}: {}\n'.format(key, items[db.room_container][key]) for key in sorted(items[db.room_container])]
        if len(room_items) > 0:
            ret += '\nRoom aspects:\n{}'.format('\n'.join(room_items))
    send(bot, chat_id, ret)

@add_command('player')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_args(1, 'Please specify the player name like this: `/player <name>`.')
@check_too_many_games
def player(bot, dbc, chat_id, sender_id, gameid, input_args, *args, **kwargs):
    new_player_added = db.add_player(dbc, sender_id, input_args[1], gameid, db.ROLE_PLAYER)
    if new_player_added:
        template = db.get_template_from_gameid(dbc, gameid)
        db.add_default_items(dbc, sender_id, gameid, template)
        send(bot, chat_id, 'Welcome, {}.'.format(input_args[1]))
    else:
        send(bot, chat_id, 'You will now be known as {}.'.format(input_args[1]))

@add_command('update')
@add_command('add')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_args(2, 'Use the format: /add <container> <key> [change].')
def add(bot, dbc, chat_id, gameid, command, sender_id, input_args, *args, **kwargs):
    if command == '/add' and db.number_of_items(dbc, gameid, sender_id) > 50:
        send(bot, chat_id, 'You exceeded the maximum number of items. Please delete some first.')
        return
    container = input_args[1]
    key = input_args[2]
    if len(input_args) <= 3:
        change = '+1'
    else:
        change = ' '.join(input_args[3:])
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    if command == 'update':
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

@add_command('addlist')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_args(2, 'Use the format: /addlist <container> <description>.')
def addlist(bot, dbc, chat_id, gameid, sender_id, command, input_args, *args, **kwargs):
    if db.number_of_items(dbc, gameid, sender_id) > 50:
        send(bot, chat_id, 'You exceeded the maximum number of items. Please delete some first.')
        return
    container = input_args[1]
    description = ' '.join(input_args[2:])
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    db.add_to_list(dbc, gameid, owner, container, description)
    send(bot, chat_id, 'Added "{}" to container {}.'.format(description, container))

@add_command('del')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_args(2, 'Use the format: /del <container> <key>.')
def delitem(bot, dbc, chat_id, gameid, command, sender_id, input_args, *args, **kwargs):
    container = input_args[1]
    key = input_args[2]
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    oldvalue = db.delete_item(dbc, gameid, owner, container, key)
    if oldvalue == None:
        send(bot, chat_id, 'Item {}/{} not found.'.format(container, key))
    else:
        send(bot, chat_id, 'Deleted {}/{} (was {}).'.format(container, key, oldvalue))

@add_command('show')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
def show(bot, dbc, sender_id, chat_id, gameid, command, input_args, *args, **kwargs):
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

@add_command('roll')
@add_command('r')
@add_command('gmroll')
@need_gameid(mustbenone=None)
def roll(bot, dbc, chat_id, gameid, sender_id, command, input_args, *args, **kwargs):
    
    if len(input_args) < 2:
        template = db.get_template_from_groupid(dbc, chat_id)
        if template == 'fae':
            dice = '4dF'
        else:
            # more templates here
            dice = '1d20'
    else:
        dice = input_args[1].strip()

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

    if command == 'roll' or command == 'r':
        send(bot, chat_id, 'Rolled {} = {}.'.format(description, value))
    elif command == 'gmroll':
        if gameid is None:
            send(bot, chat_id, 'You are not in a game.')
            return
        playername = db.get_player_name(dbc, gameid, sender_id)
        if playername is None:
            send(bot, chat_id, 'You are not in a game.')
            return
        masters = db.get_masters_for_game(dbc, gameid)

        try:
            send(bot, sender_id, 'You rolled {} = {}.'.format(description, value))
        except telepot.exception.TelegramError:
            send(bot, chat_id, '{}, I couldn\'t send you the roll results. Please send me a private message to allow me sending future rolls.'.format(username))
        for master in masters:
            if sender_id == master:
                continue
            try:
                send(bot, master, '{} ({}) rolled {} = {}.'.format(playername, username, description, value))
            except telepot.exception.TelegramError:
                send(bot, chat_id, '{}, I couldn\'t send you the roll results. Please send me a private message to allow me sending future rolls.'.format(username))

@add_command('start')
def start(bot, chat_id, *args, **kwargs):
    send(bot, chat_id, start_usage())

