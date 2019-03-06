import telepot
import functools
import db

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
        def wrapper(*args, bot, chat_id, input_args, **kwargs):
            if len(input_args) < 1 + number:
                bot.sendMessage(chat_id, errormessage)
                return False
            return func(*args, bot=bot, chat_id=chat_id, input_args=input_args, **kwargs)
        return wrapper 
    return decorator

def need_group(func):
    @functools.wraps(func)
    def wrapper(*args, bot, chat_id, is_group, **kwargs):
        if is_group is not True:
            bot.sendMessage(chat_id, 'You must run this command in a group.')
            return False
        return func(*args, bot=bot, chat_id=chat_id, is_group=is_group, **kwargs)
    return wrapper 

def need_gameid(mustbenone, errormessage):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, bot, dbc, chat_id, **kwargs):
            gameid = db.get_game_from_group(dbc, chat_id)
            if mustbenone and gameid is not None or not mustbenone and gameid is None:
                bot.sendMessage(chat_id, errormessage)
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
                bot.sendMessage(chat_id, errormessage)
                return False
            return func(*args, bot=bot, dbc=dbc, gameid=gameid, sender_id=sender_id, chat_id=chat_id, **kwargs)
        return wrapper 
    return decorator 


@add_command('newgame')
@need_group
@need_gameid(mustbenone=True, errormessage=newgame_already_started_usage())
@need_args(1, 'Please specify the game name like this: `/newgame <name>`.')
def newgame(bot, dbc, chat_id, sender_id, username, groupname, input_args, *args, **kwargs):
    if db.number_of_games(dbc, sender_id) > 10:
        bot.sendMessage(chat_id, 'You exceeded the maximum number of games. Please close some first.')
        return False
    gameid = db.new_game(dbc, sender_id, username, input_args[1], chat_id, groupname, 'fae')
    if gameid is None:
        bot.sendMessage(chat_id, newgame_already_started_usage())
        return False

    db.add_default_items(dbc, sender_id, gameid, 'fae')
    bot.sendMessage(chat_id, 'New game created: {}.'.format(input_args[1]))


@add_command('delgame')
@need_group
@need_gameid(mustbenone=False, errormessage='No game found.')
@need_role(db.ROLE_MASTER, 'You need to be a game master to close a game.')
def delgame(bot, dbc, chat_id, gameid, *args, **kwargs):
    db.del_game(dbc, gameid)
    bot.sendMessage(chat_id, 'GG, humans.')
