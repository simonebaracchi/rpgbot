
# rpgbot
RPG helper bot for Telegram

Commands:

  - /newgame `<name>`
  - /delgame
  - /showgame
  - /roll
  - /player `<name>`
  - /update `<container>` `<item>` `<value>`
  - /add `<container>` `<item>` `<change>`
  - /del `<container>` `<item>`
  - /show


## Run in docker

Build docker container:

```
 docker build . -t rpgbot
```


Run container:

```
 docker run -t -v /your-preferred-path/data:/data -e RPGBOT_TOKEN=Your:Token -e RPGBOT_ADMINS=my-id,another-id rpgbot
```
