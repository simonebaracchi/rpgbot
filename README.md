# rpgbot
RPG helper bot for Telegram

Commands:

  - /newgame `<name>`

Creates a new game by that name. The current group is automatically joined. The user that creates a game becomes the game master.

  - /delgame

Ends the game in the current group. Must be a game master.

  - /showgame

Show game statistics (name, players, etc.)

  - /player `<name>`

Join the game as a player, with the given character name (or update your characters name).

  - /roll `[<dice>]`

Roll dices. Defaults to 4dF. Supports regular and Fate dices, including bonus/maluses, like 2d20, 6d8+3, 8dF, 4dF-2.

  - /show

Shows your character sheet and inventory contents.

  - /add `<container>` `<item>` `<value>`

Adds an item to your character sheet or inventory. If the item does not exist, it is created. "Change" can be a text string, a number, or a relative change (i.e. if "value" has a plus or minus sign, like "+1" or "-1", the item value is changed by the specified amount).

The special container "room" will add an item to the room; it will be shared with all players, as such it is useful for setting stuff like room aspects.Items in the room can then be shown with /showgame.

The special container "rolls" will store saved rolls. They can then be recalled with `/roll`.

  - /addlist `<container>` `<item description>`

Similar to /add, but helpful when you care more about the item description, rather than its name (for example, Fate aspects are just a numbered list of effects, with no associated name).

  - /update `<container>` `<item>` `<value>`

Similar to /add, but does not create an object if it does not already exist.

  - /del `<container>` `<item>`

Delete an item (or another a character sheet entry). 

### Examples

`/add inventory short-sword 1`

`/add rolls attack 1d6+2`

`/roll attack`

`/update rolls attack 2d4+1`

`/update inventory coins +100`

`/addlist room Everything is on fire!`

`/del inventory health-potion`

