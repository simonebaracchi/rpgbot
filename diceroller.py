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
4dF +1
0dF    +0
1d4+1d6
1d4+1d6495
1d4+1d4+1d4+1d4
1d4+1dF+1
1d4+1d4+99
d4+d4+1
1d3+1+1d3+1
1d4+3+1d4
1d4+

these other should not match completely:
d
asd
asdq
8d10-
8dF-
3d1F
9dF1
9d1+1-1
9d-1
-1d3
1d4+1+1
1dn
1a3
+1
-1
"""

class InvalidFormat(Exception):
    pass
class TooManyDices(Exception):
    pass

"""
Returns:
the dice description (e.g. 4dF+3); the actual rolled value (e.g. 6); the outcome description (e.g. 3+4+2+4)
"""
def roll(dice):
    """
    dice - a dice string, like 2d10, 6dF, 1d2+1, and so on
    """

    ret = 0
    outcome = ''
    m = re.finditer('([0-9]+)?d([0-9]+|[Ff])\s*(?:([\+\-])([0-9]+)(?!(?:[0-9]+)?d(?:[0-9]+|[Ff])))?(?:\+?)', dice)
    if m is None:
        raise InvalidFormat
    groups = list(m)
    matched = ''.join(x.group() for x in groups)
    if dice != matched:
        raise InvalidFormat


    bonus = None
    dice_description = ''
    dices_list = []
    for g in groups:
        if g.group(4) is not None:
            bonus = 0 if bonus is None else bonus
            try:
                if g.group(3) == '+':
                    bonus += int(g.group(4))
                elif g.group(3) == '-':
                    bonus -= int(g.group(4))
                else:
                    raise InvalidFormat
            except:
                raise InvalidFormat
        
        dices_list.append((g.group(1), g.group(2)))

    for dice in dices_list:
        dices = dice[0] 
        sides = dice[1]

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

        if dice_description is not '':
            dice_description += '+'
        dice_description += '{}d{}'.format(dices_int, sides)

        # roll dice
        if sides == 'F':
            # Fate dice
            for i in range(0, dices_int):
                value = random.randint(-1, 1)
                ret += value;
                if value == -1:
                    outcome += '➖'
                if value == 0:
                    outcome += '〇'
                if value == 1:
                    outcome += '➕'
        else:
            # DnD dice
            lista = []
            for x in range(0, dices_int):
                value = random.randint(1, sides_int);
                ret += value
                lista.append(str(value))
            if outcome != '':
                outcome += '+'
            if len(dices_list) > 1 and dices_int > 1:
                outcome += '('
            outcome += '+'.join(lista)
            if len(dices_list) > 1 and dices_int > 1:
                outcome += ')'


    if bonus is not None:
        if bonus >= 0:
            dice_description += '+{}'.format(bonus)
            outcome += '(+{})'.format(bonus)
        else:
            dice_description += '{}'.format(bonus)
            outcome += '({})'.format(bonus)
        ret += bonus
        
    return dice_description, ret, outcome

