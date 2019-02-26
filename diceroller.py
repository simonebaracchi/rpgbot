import re
import random

"""
Want more dices? 
First check these keep working in a regex tester (like regex101)
1d1
0d1
110000d10000
9999d99999
9d1+999
119d111-111
4dF
0dF
4dF+1
4dF-1
d20
dF
d20+1
dF+3
4df
0df
4df+1
4df-1
df
df+3

these other should be rejected:
8d10-
8dF-
3d1F
9dF1
9d1+1-1
9d-1
-1d3
1dn
1a3
"""

class InvalidFormat(Exception):
    pass
class TooManyDices(Exception):
    pass

def roll(dice):
    """
    dice - a dice string, like 2d10, 6dF, 1d2+1, and so on
    """

    ret = 0
    string = ''
    m = re.search('^([0-9]+)?d([0-9]+|[Ff])(?:([\+\-])([0-9]+))?$', dice)
    if m is not None:
        # DnD dice
        dices = m.group(1)
        sides = m.group(2)
        bonustype = m.group(3)
        bonus = m.group(4)
    else:
        raise InvalidFormat

    # check number of sides
    sides_int = 0
    if sides == 'F' or sides == 'f':
        sides = 'F'
    else:
        try:
            sides_int = int(sides)
        except:
            raise InvalidFormat
        if sides_int > 10000:
            raise TooManyDices
        if sides_int <= 0:
            raise InvalidFormat

    # check number of dices
    dices_int = 0
    if dices is None:
        if sides == 'F':
            dices_int = 4
        else:
            dices_int = 1
    else:
        try:
            dices_int = int(dices)
        except:
            raise InvalidFormat
    if dices_int > 100:
        raise TooManyDices
    if dices_int <= 0:
        raise InvalidFormat

    # check bonus type
    bonus_mult = None
    if bonustype == None:
        pass
    elif bonustype == '+':
        bonus_mult = 1
    elif bonustype == '-':
        bonus_mult = -1
    else:
        raise InvalidFormat

    # check bonus
    if bonus is not None:
        try:
            bonus = int(bonus)
        except:
            raise InvalidFormat
        
    # roll dice
    if sides == 'F':
        # Fate dice
        for i in range(0, dices_int):
            value = random.randint(-1, 1)
            ret += value;
            if value == -1:
                string += '➖'
            if value == 0:
                string += '〇'
            if value == 1:
                string += '➕'
    else:
        # DnD dice
        lista = []
        for x in range(0, dices_int):
            value = random.randint(1, sides_int);
            ret += value
            lista.append(str(value))
        string = '+'.join(lista)

    if bonus_mult is not None and bonus is not None:
        ret += bonus_mult * bonus
        string += '(' + bonustype + str(bonus) + ')'

    return ret, string

