# GiveawaySnake

A simple bot made with [discord.py](https://discordpy.readthedocs.io/en/latest/) to quickly manage giveaways on your server!

-------------------------------------------

## Features

- 5 Giveaway Commands: `create`, `start`, `end`, `delete`, `reroll` 
- Automatic restarting of giveaways after restart
- Dynamic refresh intervals
- Customisable Prefix
- Customisable Giveaway Role (Allows members to host giveaways)

## Setup

Create a file `config.py` in the root directory, like this
```py
TOKEN="YOUR_TOKEN_HERE"
MONGO_URI="MONGODB_CONNECTION_URI"
```