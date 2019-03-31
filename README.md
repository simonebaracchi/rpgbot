
# rpgbot
RPG helper bot for Telegram. Manages character sheets, dice rolls, and game state.

**Want to try it?** Message @character_sheet_bot on Telegram.

I wrote this as a very generic tool for pen-and-paper RPGs, but via Telegram. Character sheets are fully custom and are structured as "container - key - value" data. It is up to you what your character sheet is made up of, except for a "template" sheet (based on Fate Accelerated RPG) that is automatically generated for new players, but it can be fully customized afterwards.

Commands:

  - `/newgame <name>`

Creates a new game by that name. Must be used in a Telegram group chat, the game will run in the current group. The user that creates a game becomes the game master. Other players can join with `/player <name>` (see below).

  - `/delgame`

Ends the game in the current group. Must be a game master to use it.

  - `/showgame`

Show game statistics (name, players, etc.)

  - `/player <name>`

Join the game as a player, with the given character name (or update your characters name if you already joined the game).

  - `/roll [<dice>]`

Roll dices. Defaults to 4dF. Supports regular and Fate dices, including bonus/maluses, like 2d20, 6d8+3, 8dF, 4dF-2.

Saved rolls can be defined with `/add rolls` and `/update rolls` (see below).

  - `/gmroll [<dice>]`

Similar to `/roll`, but sends the results via private message to the user and the game master(s). Due to Telegram restrictions on private message, you will have to send a private message to the bot before being able to receive rolls privately.

  - `/show`

Shows your character sheet and inventory contents.

  - `/add <container> <item> [<value>]`

Adds an item to your character sheet. If the item does not exist, it is created. "Change" can be a text string, a number, or a relative change (i.e. if "value" has a plus or minus sign, like "+1" or "-1", the item value is changed by the specified amount). If "change" is not specified, "+1" is implicitly used.

It can be used to add anything to your character sheet, e.g. your character description, skills, spells, inventory items, etc.

The special container "room" will add an item to the room; it will be shared with all players in the group, as such it is useful for setting stuff like room aspects. Items in the room can then be shown with /showgame.

The special container "rolls" will store saved rolls. Use the dice definition (e.g. `1d20+1`) as value. They can then be recalled with `/roll`.

  - `/addlist <container> <item description>`

Similar to /add, but helpful when you care more about the item description, rather than its name (for example, Fate aspects are just a numbered list of effects, with no associated name).

  - `/update <container> <item> [<value>]`

Similar to /add, but does not create an object if it does not already exist.

  - `/del <container> <item>`

Delete an item (or another a character sheet entry). 

### Examples

`/newgame The tales of Github` (starts a new game with this name; the user starting the game becomes the game master)

`/player Octocat` (renames your character to Octocat, or, joins the game with that name)

`/show` (check your character sheet contents)

`/update gen highconcept He is the ultimate keeper of the Source.` (changes the high concept in your character sheet)

`/add inventory short-sword` (add an item named "short-sword" to the container "inventory" with a default value of 1)

`/add rolls attack 1d6+2` (saves a roll named "attack" with value 1d6+2)

`/roll attack` (rolls the previously saved dice)

`/update rolls attack 2d4+1` (changes the previosly saved roll to a different dice, 2d4+1)

`/update inventory coins +100` (adds 100 coins to your inventory; will fail if you don't have an item by that name already)

`/update gen fatepoints` (increases your fatepoint by 1)

`/update gen fatepoints -1` (decreases your fatepoint by 1)

`/addlist room Everything is on fire!` (add an item on the room instead of yourself; can be seen with /showgame)

`/del inventory health-potion` (deletes all items named "health-potion" from your inventory)

`/showgame` (shows the game state, such as, its name, the players, the gm, the room aspects)

## Run in docker

Build docker container:
```
 docker build . -t rpgbot
```


Run container:
```
 docker run -t -v /your-preferred-path/data:/data -e RPGBOT_TOKEN=<Telegram-token> -e RPGBOT_ADMINS=<my-id,another-id> rpgbot
```

## Run without docker

Configure `custom_config.py` manually or through `install.py` and then run:

```
# python3 main.py
```

