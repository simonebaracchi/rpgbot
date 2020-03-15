import telepot
import functools
from collections import OrderedDict

import db
import diceroller

all_commands = {}

def newgame_already_started_usage():
    return """This game was already started in this group.
Now invite some players, make them join with `/player <character name>`, check your characters with `/show`, adjust your character sheet with `/update`, and roll dices with `/roll`.
For a more complete list of commands, see https://github.com/simonebaracchi/rpgbot."""


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
        def wrapper(handler):
            if len(handler.args) < 1 + number:
                handler.send(errormessage)
                return False
            return func(handler)
        return wrapper 
    return decorator

def read_args(string, argname):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler, **kwargs):
            handler.send(string, allowedit=True)
            handler.read_answer(func, argname, kwargs)
        return wrapper 
    return decorator

def choose_container(string, argname, allownew, adding):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler, **kwargs):
            items = db.get_items(handler.dbc, handler.group.gameid, handler.sender_id)
            room = db.get_items(handler.dbc, handler.group.gameid, handler.chat_id)
            options = OrderedDict()
            if adding:
                # show special containers even if empty
                options['Room items'] = db.room_container
                options['Saved rolls'] = db.rolls_container
            else:
                # show special containers if not empty
                if db.room_container in room:
                    options['Room items'] = db.room_container
                if db.rolls_container in items:
                    options['Saved rolls'] = db.rolls_container
            for container in items.keys():
                if container == db.rolls_container:
                    continue
                else:
                    options[container] = container
            if allownew:
                options['New container...'] = '__new__container__'
                handler.send(string, options=options, allowedit=True)
                kwargs['containercallback'] = func
                kwargs['argname'] = argname
                handler.read_answer(new_container_callback, 'newcontainer', kwargs)
            elif len(options) == 0:
                # no options to show
                handler.send('You don\'t seem to have anything with you.')
                return False
            else:
                handler.send(string, options=options, allowedit=True)
                handler.read_answer(func, argname, kwargs)
        return wrapper 
    return decorator

def choose_another_player(string, argname):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler, **kwargs):
            players = db.get_all_players_from_game(handler.dbc, handler.group.gameid)
            options = OrderedDict()
            for p in players:
                options[p.playername] = p.playerid
            handler.send(string, options=options, allowedit=True)
            handler.read_answer(func, argname, kwargs)
        return wrapper 
    return decorator

def new_container_callback(handler, newcontainer, argname, containercallback, **kwargs):
    if newcontainer == '__new__container__':
        handler.send('How do you want to name the container?', allowedit=True)
        handler.read_answer(containercallback, argname, kwargs)
    else:
        kwargs[argname] = newcontainer
        return containercallback(handler, **kwargs)

def choose_item(string, argname):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler, container, **kwargs):
            if container == db.room_container:
                items = db.get_items(handler.dbc, handler.group.gameid, handler.chat_id)
            else: 
                items = db.get_items(handler.dbc, handler.group.gameid, handler.sender_id)
            options = OrderedDict()
            for key, value in items[container].items():
                options['{} ({})'.format(key, value)] = key
            handler.send(string, options=options, allowedit=True)
            kwargs['container'] = container
            handler.read_answer(func, argname, kwargs)
        return wrapper 
    return decorator

def choose_template(string, argname):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler, **kwargs):
            options = OrderedDict()
            for key, value in db.game_templates.items():
                options[value] = key
            handler.send(string, options=options, allowedit=True)
            handler.read_answer(func, argname, kwargs)
        return wrapper 
    return decorator

def need_group(func):
    @functools.wraps(func)
    def wrapper(handler):
        if handler.is_group is not True:
            handler.send('You must run this command in a group.')
            return False
        return func(handler)
    return wrapper 

def check_too_many_games(func):
    @functools.wraps(func)
    def wrapper(handler):
        if db.number_of_games(handler.dbc, handler.sender_id) > 1:
            handler.send('Sorry, only one game at a time is currently supported.')
            return False
        return func(handler)
    return wrapper 

def need_gameid(allownotexisting=False, allowexisting=False, errormessage=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler):
            group = handler.group
            player = None
            if group is None:
                group, player = db.get_group_from_playerid(handler.dbc, handler.sender_id)
            
            handler.group = group
            handler.player = player
            if (allowexisting is False and group is not None) or (allownotexisting is False and group is None):
                handler.send(errormessage)
                return False
            return func(handler)
        return wrapper 
    return decorator 

def get_default_group(func):
    @functools.wraps(func)
    def wrapper(handler):
        if handler.is_group is True and handler.group is None:
            # Not in a game
            handler.group = db.get_group_from_groupid(handler.dbc, handler.chat_id)
        return func(handler)
    return wrapper 

def need_role(role, errormessage):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(handler):
            user_role = db.get_player_role(handler.dbc, handler.sender_id, handler.group.gameid)
            if user_role != role:
                handler.send(errormessage)
                return False
            return func(handler)
        return wrapper 
    return decorator 


@add_command('newgame')
@need_group
@need_gameid(allownotexisting=True, errormessage=newgame_already_started_usage())
#@need_args(1, 'Please specify the game name like this: `/newgame <name>`.')
@check_too_many_games
@read_args('How are we going to call the game?', 'name')
@choose_template('Please choose a game template. This will only affect the default character sheets and dices.', 'template')
def newgame(handler, name, template):
    template, skip_sheet = db.convert_template(template)
    gameid = db.new_game(handler.dbc, handler.sender_id, handler.username, name, handler.chat_id, handler.groupname, template)
    if gameid is None:
        handler.send(newgame_already_started_usage())
        return False

    if not skip_sheet:
        db.add_default_items(handler.dbc, handler.sender_id, gameid, template)
    handler.send('New game created: {}.'.format(name))


@add_command('delgame')
@need_group
@need_gameid(allowexisting=True, errormessage='No game found.')
@need_role(db.ROLE_MASTER, 'You need to be a game master to close a game.')
def delgame(handler):
    db.del_game(handler.dbc, handler.group.gameid)
    handler.send('GG, humans.')
    handler.group = None

@add_command('showgame')
@need_gameid(allowexisting=True, errormessage='No game found.')
def showgame(handler):
    gamename, template, groups, players = db.get_game_info(handler.dbc, handler.group.gameid)
    players_string = [x + (' (gm)' if (y == db.ROLE_MASTER) else '') for x,y in players.items()]
    ret = '{} ({})\nGroups: {}\nPlayers: {}'.format(gamename, db.game_templates[template], ', '.join(groups), ', '.join(players_string))

    items = db.get_items(handler.dbc, handler.group.gameid, handler.chat_id)
    if db.room_container in items:
        room_items = ['  - {}: {}\n'.format(key, items[db.room_container][key]) for key in sorted(items[db.room_container])]
        if len(room_items) > 0:
            ret += '\nRoom aspects:\n{}'.format('\n'.join(room_items))
    handler.send(ret)

@add_command('player')
@need_group
@get_default_group
@need_gameid(allowexisting=True, allownotexisting=True, errormessage='No game found.')
#@need_args(1, 'Please specify the player name like this: `/player <name>`.')
@check_too_many_games
@read_args('What is your name, adventurer?', 'name')
def player(handler, name):
    new_player_added = db.add_player(handler.dbc, handler.sender_id, name, handler.group.gameid, db.ROLE_PLAYER)
    if new_player_added:
        template = db.get_template_from_gameid(handler.dbc, handler.group.gameid)
        db.add_default_items(handler.dbc, handler.sender_id, handler.group.gameid, template)
        handler.send('Welcome, {}.'.format(name))
    else:
        handler.send('You will now be known as {}.'.format(name))

@add_command('add')
@need_gameid(allowexisting=True, errormessage='No game found.')
#@need_args(2, 'Use the format: /add <container> <key> [change].')
@choose_container('In which container?', 'container', allownew=True, adding=True)
@read_args('What item would you like to add?', 'key')
@read_args('What would you like to set it to?', 'change')
def add(handler, container, key, change):
    command = handler.command
    return add_or_update_item(handler, container, key, change, command)

@add_command('update')
@need_gameid(allowexisting=True, errormessage='No game found.')
#@need_args(2, 'Use the format: /add <container> <key> [change].')
@choose_container('In which container?', 'container', allownew=False, adding=False)
@choose_item('Which item?', 'key')
@read_args('What would you like to set it to?', 'change')
def update(handler, container, key, change):
    command = handler.command
    return add_or_update_item(handler, container, key, change, command)

def add_or_update_item(handler, container, key, change, command):
    dbc = handler.dbc
    gameid = handler.group.gameid
    sender_id = handler.sender_id
    chat_id = handler.chat_id

    if command == '/add' and db.number_of_items(dbc, gameid, sender_id) > 50:
        handler.send('You exceeded the maximum number of items. Please delete some first.')
        return
    #container = input_args[1]
    #key = input_args[2]
    #if len(input_args) <= 3:
    #   change = '+1'
    #else:
    #    change = ' '.join(input_args[3:])
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    if command == 'update':
        replace_only = True
    else:
        replace_only = False
    oldvalue, newvalue = db.update_item(dbc, gameid, owner, container, key, change, replace_only)
    if newvalue is None:
        handler.send('Item {}/{} not found.'.format(container, key))
    elif isinstance(oldvalue, int) and isinstance(newvalue, int):
        handler.send('Updated {}/{} from {} to {} (changed {}).'.format(container, key, 
             oldvalue, newvalue, newvalue-oldvalue))
    else:
        handler.send('Updated {}/{} to "{}".'.format(container, key, newvalue))


@add_command('addlist')
@need_gameid(allowexisting=True, errormessage='No game found.')
#@need_args(2, 'Use the format: /addlist <container> <description>.')
@choose_container('In which container?', 'container', allownew=True, adding=True)
@read_args('What would you like to add?', 'description')
def addlist(handler, container, description):
    dbc = handler.dbc
    gameid = handler.group.gameid
    sender_id = handler.sender_id
    chat_id = handler.chat_id

    if db.number_of_items(dbc, gameid, sender_id) > 50:
        handler.send('You exceeded the maximum number of items. Please delete some first.')
        return
    #container = input_args[1]
    #description = ' '.join(input_args[2:])
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    db.add_to_list(dbc, gameid, owner, container, description)
    handler.send('Added "{}" to container {}.'.format(description, container))

@add_command('del')
@need_gameid(allowexisting=True, errormessage='No game found.')
@choose_container('In which container?', 'container', allownew=False, adding=False)
@choose_item('Which item?', 'key')
def delitem(handler, container, key):
    dbc = handler.dbc
    gameid = handler.group.gameid
    sender_id = handler.sender_id
    chat_id = handler.chat_id

    #container = input_args[1]
    #key = input_args[2]
    owner = sender_id
    if container == db.room_container:
        owner = chat_id
    oldvalue = db.delete_item(dbc, gameid, owner, container, key)
    if oldvalue == None:
        handler.send('Item {}/{} not found.'.format(container, key))
    else:
        handler.send('Deleted {}/{} (was {}).'.format(container, key, oldvalue))

def show_player(handler, playerid=None):
    dbc = handler.dbc
    gameid = handler.group.gameid
    items = db.get_items(dbc, gameid, playerid)
    playername = db.get_player_name(dbc, gameid, playerid)
    if playername is None:
        handler.send('You are not in a game.')
        return
    ret = ''
    ret += 'Character sheet for {}:\n'.format(playername)
    if items is None:
        handler.send('No items found.')
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
        for key in sorted(items[container]):
            ret += '  - {} ({})\n'.format(key, items[container][key])
    handler.send(ret)

@add_command('show')
@need_gameid(allowexisting=True, errormessage='No game found.')
def show(handler):
    return show_player(handler, handler.sender_id)

@add_command('showother')
@need_gameid(allowexisting=True, errormessage='No game found.')
@choose_another_player('Which player?', 'playerid')
def showother(handler, playerid):
    return show_player(handler, playerid)

@add_command('roll')
@add_command('r')
@add_command('gmroll')
@need_gameid(allowexisting=True, allownotexisting=True)
def roll(handler):
    dbc = handler.dbc
    username = handler.username
    gameid = None
    groupid = None
    if handler.group is not None:
        gameid = handler.group.gameid
        groupid = handler.group.groupid
    sender_id = handler.sender_id
    args = handler.args if handler.args is not None else []
    command = handler.command
    
    if len(args) < 2:
        template = db.get_template_from_groupid(dbc, groupid)
        if template == 'fae':
            dice = '4dF'
        else:
            # more templates here
            dice = '1d20'
    else:
        dice = args[1].strip()

    value = 0
    outcome = ''
    description = ''
    
    invalid_format = False
    try:
        description, value, outcome = diceroller.roll(dice)
    except (diceroller.InvalidFormat):
        invalid_format = True
    except (diceroller.TooManyDices):
        handler.send('Sorry, try with less dices.')
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
                description, value, outcome = diceroller.roll(dice)
            except (diceroller.InvalidFormat):
                invalid_format = True
            except (diceroller.TooManyDices):
                handler.send('Sorry, try with less dices.')
                return

    if invalid_format:
        handler.send('Invalid dice format.')
        return

    if command == 'roll' or command == 'r':
        handler.send('Rolled {} = {}.'.format(outcome, value))
    elif command == 'gmroll':
        if gameid is None:
            handler.send('You are not in a game.')
            return
        playername = db.get_player_name(dbc, gameid, sender_id)
        if playername is None:
            handler.send('You are not in a game.')
            return
        masters = db.get_masters_for_game(dbc, gameid)

        handler.send('{} secretly rolls {}...'.format(playername, description))
        try:
            handler.send('You rolled {} = {}.'.format(outcome, value), target=sender_id)
        except telepot.exception.TelegramError:
            handler.send('{}, I couldn\'t send you the roll results. Please send me a private message to allow me sending future rolls.'.format(username))
        for master in masters:
            if sender_id == master:
                continue
            try:
                handler.send('{} ({}) rolled {} = {}.'.format(playername, username, outcome, value), target=master)
            except telepot.exception.TelegramError:
                handler.send('{}, I couldn\'t send you the roll results. Please send me a private message to allow me sending future rolls.'.format(username))


@add_command('start')
@need_gameid(allownotexisting=True, allowexisting=True)
def start(handler):
    if handler.is_group is False and handler.group is None:
        # I am in a private chat, suggest to add me to a group
        message = """Howdy, human.
I am a character sheet bot for Fate RPG.
To use my services, add me to a group, invite other players, and call me again to start a new game.
Use the inline keyboard to navigate my character sheet functions, or use the shortcut `/roll` to roll dices.
Visit the official site for more details.

Hope you have fun!"""
        options = OrderedDict()
        options['Go to official site ->'] = {'url': 'https://github.com/simonebaracchi/rpgbot'}
        handler.send(message, options=options, allowedit=True)
    elif handler.is_group is True and handler.group is None:
        # I am in a group,
        gameid = db.get_game_from_group(handler.dbc, handler.chat_id)
        if gameid is not None:
            # caller is not in game, but a game is ongoing
            options = OrderedDict()
            options['Join game'] = 'player'
            options['Roll dices (shortcut: /roll <dice>)'] = 'roll'
            handler.send('How can I help you?', options=options, allowedit=True)
        else:
            # suggest to start a new game
            message = """Howdy, earthlings.
I am a character sheet bot for Fate RPG.
How can I help you?"""
            options = OrderedDict()
            options['Start new game'] = 'newgame'
            options['Roll dices (shortcut: /roll <dice>)'] = 'roll'
            options['Go to official site ->'] = {'url': 'https://github.com/simonebaracchi/rpgbot'}
            handler.send(message, options=options, allowedit=True)
    elif handler.is_group is False and handler.group is not None:
        # I am in a private chat with a player
        options = OrderedDict()
        subopts = OrderedDict()
        subopts['Show game status'] = 'showgame'
        subopts['Show player status'] = 'show'
        options['dummy'] = subopts
        options['Show other player status'] = 'showother'

        subopts = OrderedDict()
        subopts['Add item'] = 'add'
        subopts['Update item'] = 'update'
        subopts['Add list item'] = 'addlist'
        subopts['Delete item'] = 'del'
        options['dummy2'] = subopts

        options['Roll dices (shortcut: /roll <dice>)'] = 'roll'
        options['Roll dices secretly (shortcut: /gmroll)'] = 'gmroll'

        subopts = OrderedDict()
        subopts['Go to official site ->'] = {'url': 'https://github.com/simonebaracchi/rpgbot'}
        subopts['Cancel'] = 'cancel'
        options['dummy3'] = subopts

        handler.send('How can I help you?', options=options, allowedit=True)
    else:
        # Game is started in the group!
        options = OrderedDict()
        subopts = OrderedDict()
        subopts['Show game status'] = 'showgame'
        subopts['Show player status'] = 'show'
        options['dummy'] = subopts

        subopts = OrderedDict()
        subopts['Add item'] = 'add'
        subopts['Update item'] = 'update'
        subopts['Add list item'] = 'addlist'
        subopts['Delete item'] = 'del'
        options['dummy2'] = subopts

        options['Roll dices (shortcut: /roll <dice>)'] = 'roll'
        options['Roll dices secretly (shortcut: /gmroll)'] = 'gmroll'
        subopts = OrderedDict()
        subopts['More ...'] = 'more'
        subopts['Cancel'] = 'cancel'
        options['dummy3'] = subopts
        handler.send('How can I help you?', options=options, allowedit=True)
        

@add_command('more')
@need_group
@need_gameid(allowexisting=True)
def more(handler):
    # More options when game is started...
    options = OrderedDict()
    options['Show other player status'] = 'showother'
    options['Change player name'] = 'player'
    #options['Leave game'] = 'leave'
    options['Delete game'] = 'delgame'
    options['Go to official site ->'] = {'url': 'https://github.com/simonebaracchi/rpgbot'}
    subopts = OrderedDict()
    subopts['<- Back'] = 'start'
    subopts['Cancel'] = 'cancel'
    options['dummy'] = subopts
    handler.send('How can I help you?', options=options, allowedit=True)

@add_command('cancel')
def cancel(handler):
    handler.delete()

