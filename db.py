import sqlite3
import config

db_name = config.db_file
db_version = 1
ROLE_PLAYER = 10
ROLE_MASTER = 20
game_templates = ['fae']
room_container = 'room'
rolls_container = 'rolls'

def open_connection():
    return sqlite3.connect(db_name)
def close_connection(db):
    db.close()

def table_exists(db, table):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?''', (table,))
    result = query.fetchone()
    if result[0] == 0:
        return False
    else:
        return True

class Group():
    def __init__(self, gameid, groupid, groupname):
        self.gameid = gameid
        self.groupid = groupid
        self.groupname = groupname

class Player():
    def __init__(self, gameid, playerid, role, playername):
        self.gameid = gameid
        self.playerid = playerid
        self.role = role
        self.playername = playername

def init():
    db = open_connection()
    try:
        print('Initializing database...')
        c = db.cursor()
        if not table_exists(db, 'Games'):
            c.execute('''CREATE TABLE IF NOT EXISTS Games (gameid integer primary key autoincrement, version int, lastactivity datetime, gamename text, template text)''')
        if not table_exists(db, 'Groups'):
            c.execute('''CREATE TABLE IF NOT EXISTS Groups (gameid integer, groupid integer primary key, groupname text)''')
        if not table_exists(db, 'Players'):
            c.execute('''CREATE TABLE IF NOT EXISTS Players (gameid integer, playerid integer, role integer, playername text, PRIMARY KEY(gameid, playerid))''')
        if not table_exists(db, 'Contents'):
            c.execute('''CREATE TABLE IF NOT EXISTS Contents (gameid integer, playerid integer, container text, key text, value text, PRIMARY KEY(gameid, playerid, container, key))''')
    except:
        print('failed to initialize database')
        raise
    db.commit()
    close_connection(db)

def new_game(db, admin, playername, gamename, groupid, groupname, template):
    """
    Creates a new game.
    DOES NOT CHECK that the group is not already in a game.
    Returns:
    None - the group is already in a game.
    the gameid otherwise.
    """
    if template not in game_templates:
        raise
    c = db.cursor()
    try:
        query = c.execute('''INSERT INTO Games(version, lastactivity, gamename, template) VALUES (?, datetime('now'), ?, ?)''', (db_version, gamename, template))
    except sqlite3.IntegrityError:
        # probably group is already in game
        return None
    gameid = c.lastrowid
    try:
        query = c.execute('''INSERT INTO Groups(gameid, groupid, groupname) VALUES (?, ?, ?)''', (gameid, groupid, groupname,))
    except sqlite3.IntegrityError:
        return None
    add_player(db, admin, playername, gameid, ROLE_MASTER)
    db.commit()
    return gameid

def del_game(db, gameid):
    c = db.cursor()
    query = c.execute('''DELETE FROM Games WHERE gameid=?''', (gameid,))
    query = c.execute('''DELETE FROM Groups WHERE gameid=?''', (gameid,))
    query = c.execute('''DELETE FROM Players WHERE gameid=?''', (gameid,))
    query = c.execute('''DELETE FROM Contents WHERE gameid=?''', (gameid,))
    db.commit()

def get_template_from_gameid(db, gameid):
    c = db.cursor()
    query = c.execute('''SELECT template FROM Games WHERE gameid=?''', (gameid,))
    result = query.fetchone()
    if result == None:
        # invalid gameid or database not updated
        raise
    template = result[0]
    return template

def get_template_from_groupid(db, groupid):
    c = db.cursor()
    query = c.execute('''SELECT template FROM Games LEFT JOIN Groups ON Games.gameid = Groups.gameid WHERE groupid=?''', (groupid,))
    result = query.fetchone()
    if result == None:
        # group not in a game
        return None
    template = result[0]
    return template

def get_group_from_playerid(db, playerid):
    c = db.cursor()
    query = c.execute('''SELECT Groups.gameid, groupid, groupname, playerid, role, playername FROM Groups LEFT JOIN Players ON Groups.gameid = Players.gameid WHERE playerid=?''', (playerid,))
    result = query.fetchone()
    if result is None:
        return None, None
    group = Group(result[0], result[1], result[2])
    player = Player(result[0], result[3], result[4], result[5])
    return group, player
    
def get_player_role(db, userid, gameid):
    c = db.cursor()
    query = c.execute('''SELECT role FROM Players WHERE playerid=? AND gameid=?''', (userid, gameid,))
    result = query.fetchone()
    if result is None:
        return None
    role = result[0]
    return role

def get_player_name(db, gameid, userid):
    c = db.cursor()
    query = c.execute('''SELECT playername FROM Players WHERE playerid=? AND gameid=?''', (userid, gameid,))
    result = query.fetchone()
    if result is None:
        return None
    name = result[0]
    return name

def add_player(db, userid, username, gameid, role):
    old_role = get_player_role(db, userid, gameid)

    new_player_added = False
    if old_role is None:
        new_player_added = True
    else:
        if old_role >= role:
            role = old_role

    c = db.cursor()
    query = c.execute('''INSERT OR REPLACE INTO Players(gameid, playerid, role, playername) VALUES (?, ?, ?, ?)''', (gameid, userid, role, username,))
    db.commit()
    return new_player_added

def get_masters_for_game(db, gameid):
    c = db.cursor()
    query = c.execute('''SELECT playerid FROM Players WHERE role=? AND gameid=?''', (ROLE_MASTER, gameid, ))
    ret = []
    for player in query:
        ret.append(player[0])
    return ret

def get_all_players_from_game(db, gameid):
    c = db.cursor()
    query = c.execute('''SELECT gameid, playerid, role, playername FROM Players WHERE gameid=?''', (gameid, ))
    ret = []
    for player in query:
        p = Player(player[0], player[1], player[2], player[3])
        ret.append(p)
    return ret

preferred_container_order = ['gen', 'aspects', 'stunts', 'skills', 'spells', 'inventory', 'rolls']
preferred_key_order = {'gen': ['highconcept', 'description', 'fatepoints', 'stress2', 'stress4', 'stress6']}

def add_default_items(db, userid, gameid, template):
    if template == 'fae':
        update_item(db, gameid, userid, 'gen', 'description', 'Describe your character in a few words.', False)
        update_item(db, gameid, userid, 'gen', 'highconcept', 'Set this to your high concept.', False)
        update_item(db, gameid, userid, 'gen', 'trouble', 'Your character\'s trouble.', False)
        update_item(db, gameid, userid, 'gen', 'fatepoints', '3', False)
        update_item(db, gameid, userid, 'gen', 'refresh', '3', False)
        update_item(db, gameid, userid, 'gen', 'stress2', 'Inactive', False)
        update_item(db, gameid, userid, 'gen', 'stress4', 'Inactive', False)
        update_item(db, gameid, userid, 'gen', 'stress6', 'Inactive', False)
        update_item(db, gameid, userid, 'stunts', '1', 'Set this to your first stunt.', False)
        update_item(db, gameid, userid, 'approaches', 'careful', '0', False)
        update_item(db, gameid, userid, 'approaches', 'clever', '0', False)
        update_item(db, gameid, userid, 'approaches', 'flashy', '0', False)
        update_item(db, gameid, userid, 'approaches', 'forceful', '0', False)
        update_item(db, gameid, userid, 'approaches', 'quick', '0', False)
        update_item(db, gameid, userid, 'approaches', 'sneaky', '0', False)
        

def number_of_games(db, user):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM Players WHERE playerid=?''', (user,))
    result = query.fetchone()
    return result[0]

def get_game_from_group(db, groupid):
    c = db.cursor()
    query = c.execute('''SELECT gameid FROM Groups WHERE groupid=?''', (groupid,))
    result = query.fetchone()
    if result is None:
        return None
    return result[0]

def get_game_info(db, gameid):
    c = db.cursor()
    query = c.execute('''SELECT gamename FROM Games WHERE gameid=?''', (gameid,))
    result = query.fetchone()
    gamename = result[0]
    query = c.execute('''SELECT groupname FROM Groups WHERE gameid=?''', (gameid,))
    groups = []
    for group in query:
        groups.append(group[0])
    query = c.execute('''SELECT playername, role FROM Players WHERE gameid=?''', (gameid,))
    players = {}
    for player in query:
        players[player[0]] = player[1]
    return gamename, groups, players

def number_of_items(db, gameid, playerid):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM Contents WHERE gameid=? AND playerid=?''', (gameid, playerid,))
    result = query.fetchone()
    return result[0]
    
def update_item(db, gameid, playerid, container, key, change, replace_only):
    """
    change: can be a string, a number, or a relative change (e.g. '+1', '-1')
    replace_only: will avoid adding a new key

    Returns:
    oldvalue: None if didn't exist, int if it was digits, or a string
    newvalue: int if oldvalue was digits and change is a relative change, text otherwise
    """
    c = db.cursor()
    query = c.execute('''SELECT value FROM Contents WHERE gameid=? AND playerid=? AND container=? AND key=?''', (gameid, playerid, container, key,))
    result = query.fetchone()
    if result is None:
        oldvalue = None
        if replace_only:
            return oldvalue, None
    else:
        oldvalue = result[0]

    if (oldvalue is None or oldvalue.isdigit()) and (change.isdigit() or (change[0] in ['+', '-'] and change[1:].isdigit())):
        if oldvalue is None:
            oldvalue = 0
        else:
            oldvalue = int(oldvalue)
        if change[0] == '+':
            newvalue = oldvalue + int(change[1:])
        elif change[0] == '-':
            newvalue = oldvalue - int(change[1:])
        else:
            newvalue = int(change)
    else:
        newvalue = change

    query = c.execute('''INSERT OR REPLACE INTO Contents(gameid, playerid, container, key, value) VALUES (?, ?, ?, ?, ?)''', (gameid, playerid, container, key, newvalue,))
    db.commit()
    return oldvalue, newvalue

def to_number(thing):
    """
    Converts something to an integer.
    Returns the integer upon success, or 0 upon failure.
    """
    try:
        test = int(thing)
        return test
    except:
        return 0

def add_to_list(db, gameid, playerid, container, description):
    """
    description: the new item description
    """
    c = db.cursor()
    query = c.execute('''SELECT key FROM Contents WHERE gameid=? AND playerid=? AND container=?''', (gameid, playerid, container,))
    maximum = 0
    for keys in query:
        maximum = max(to_number(keys[0]), maximum)
    new = maximum + 1
    query = c.execute('''INSERT OR REPLACE INTO Contents(gameid, playerid, container, key, value) VALUES (?, ?, ?, ?, ?)''', (gameid, playerid, container, new, description,))
    db.commit()

def get_item_value(db, gameid, playerid, container, key):
    c = db.cursor()
    query = c.execute('''SELECT value FROM Contents WHERE gameid=? AND playerid=? AND container=? AND key=?''', (gameid, playerid, container, key,))
    result = query.fetchone()
    if result == None:
        return None
    return result[0]

def delete_item(db, gameid, playerid, container, key):
    c = db.cursor()
    query = c.execute('''SELECT value FROM Contents WHERE gameid=? AND playerid=? AND container=? AND key=?''', (gameid, playerid, container, key,))
    result = query.fetchone()
    if result == None:
        return None
    oldvalue = result[0]
    query = c.execute('''DELETE FROM Contents WHERE gameid=? AND playerid=? AND container=? AND key=?''', (gameid, playerid, container, key,))
    db.commit()
    return oldvalue

def get_items(db, gameid, playerid):
    ret = {}
    c = db.cursor()
    contents = {}
    query = c.execute('''SELECT container, key, value FROM Contents WHERE gameid=? AND playerid=?''', (gameid, playerid,))
    for row in query.fetchall():
        if row[0] not in contents:
            contents[row[0]] = {}
        contents[row[0]][row[1]] = row[2]
    return contents
