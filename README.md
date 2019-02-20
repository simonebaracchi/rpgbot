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

Roll dices. Defaults to 4dF. 

  - /show

Shows your character sheet and inventory contents.

  - /add `<container>` `<item>` `<value>`

Adds an item to your character sheet or inventory. If the item does not exist, it is created. "Change" can be a text string, a number, or a relative change (i.e. if "value" has a plus or minus sign, like "+1" or "-1", the item value is changed by the specified amount).

  - /update `<container>` `<item>` `<value>`

Similar to /add, but does not create an object if it does not already exist.

  - /del `<container>` `<item>`

Delete an item (or a character sheet entry).
