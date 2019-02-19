import sqlite3

db_name = 'games.db'
db_version = 1
ROLE_PLAYER = 10
ROLE_MASTER = 20
game_templates = ['fae']

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
    if template not in game_templates:
        raise
    c = db.cursor()
    query = c.execute('''INSERT INTO Games(version, lastactivity, gamename, template) VALUES (?, datetime('now'), ?, ?)''', (db_version, gamename, template))
    gameid = c.lastrowid
    query = c.execute('''INSERT INTO Groups(gameid, groupid, groupname) VALUES (?, ?, ?)''', (gameid, groupid, groupname,))
    add_player(db, admin, playername, gameid, ROLE_MASTER)
    db.commit()

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
    
def add_player(db, userid, username, gameid, role):
    c = db.cursor()
    query = c.execute('''SELECT role FROM Players WHERE playerid=? AND gameid=?''', (userid, gameid,))
    result = query.fetchone()

    new_player_added = False
    if result is None:
        new_player_added = True
    else:
        if result[0] >= role:
            role = result[0]

    query = c.execute('''INSERT OR REPLACE INTO Players(gameid, playerid, role, playername) VALUES (?, ?, ?, ?)''', (gameid, userid, role, username,))
    db.commit()
    return new_player_added


def add_default_items(db, userid, gameid, template):
    if template == 'fae':
        update_item(db, gameid, userid, 'gen', 'highconcept', 'Set this to your high concept.', False)
        update_item(db, gameid, userid, 'gen', 'description', 'Describe your character in a few words.', False)
        update_item(db, gameid, userid, 'gen', 'fatepoints', '2', False)
        update_item(db, gameid, userid, 'gen', 'stress2', 'Inactive', False)
        update_item(db, gameid, userid, 'gen', 'stress4', 'Inactive', False)
        update_item(db, gameid, userid, 'gen', 'stress6', 'Inactive', False)
        update_item(db, gameid, userid, 'aspects', '1', 'Set this to your first aspect.', False)
        update_item(db, gameid, userid, 'aspects', '2', 'Set this to your second aspect.', False)
        update_item(db, gameid, userid, 'stunts', '1', 'Set this to your first stunt.', False)
        

def number_of_games(db, user):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM Players WHERE playerid=?''', (user,))
    result = query.fetchone()
    return result[0]

def get_game_from_group(db, groupid):
    c = db.cursor()
    query = c.execute('''SELECT gameid FROM Groups WHERE groupid=?''', (groupid,))
    result = query.fetchone()
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
    query = c.execute('''SELECT playername FROM Players WHERE gameid=?''', (gameid,))
    players = []
    for player in query:
        players.append(player[0])
    return gamename, groups, players

def number_of_items(db, gameid, playerid):
    c = db.cursor()
    query = c.execute('''SELECT count(*) FROM Contents WHERE gameid=? AND playerid=?''', (gameid, playerid,))
    result = query.fetchone()
    return result[0]
    
def update_item(db, gameid, playerid, container, key, change, relative):
    c = db.cursor()
    query = c.execute('''SELECT value FROM Contents WHERE gameid=? AND playerid=? AND container=? AND key=?''', (gameid, playerid, container, key,))
    result = query.fetchone()
    if result is None:
        oldvalue = 0
    else:
        oldvalue = int(result[0])
    if relative:
        newvalue = oldvalue + change
    else:
        newvalue = change
    query = c.execute('''INSERT OR REPLACE INTO Contents(gameid, playerid, container, key, value) VALUES (?, ?, ?, ?, ?)''', (gameid, playerid, container, key, newvalue,))
    db.commit()
    return oldvalue, newvalue

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
    query = c.execute('''SELECT DISTINCT container FROM Contents WHERE gameid=? AND playerid=?''', (gameid, playerid,))
    for container in query.fetchall():
        inner = c.execute('''SELECT key, value FROM Contents WHERE gameid=? AND playerid=? AND container=?''', (gameid, playerid, container[0]))
        my_list = {}
        for item in inner:
            my_list[item[0]] = item[1]
        ret[container[0]] = my_list
    return ret
