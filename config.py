# Example config file
import os

admins = os.environ.get('RPGBOT_ADMINS', '')
if admins is None:
    raise Exception('No Admins Provided')

admins = admins.split(',')

bot_token = os.environ.get('RPGBOT_TOKEN')
if bot_token is None:
    raise Exception('No Token Provided')

sqlite_path = os.environ.get('RPGBOT_SQLITE_PATH', '/data/games.db' )
