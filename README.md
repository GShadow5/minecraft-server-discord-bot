# minecraft-server-discord-bot

A simple discord bot written in python for managing multiple minecraft servers through the same discord server. 

## Features

- Manages an arbitrary number of minecraft servers (and makes sure only one server is active at a time)
- Enables players to list, start, and stop servers from the discord server
- Can force stop a server if it hangs
- Listens to both discord and minecraft chat and forwards them back and forth so that the users in game and on discord can chat together
- Enables sending commands to the currently running server via discord
- Uses a simple json file to store the servers the bot can manage, including the path to the server folder, the server name, and the command to start the server (for instance a script file or directly calling a jar)


## Installation

1. Clone the repository
2. Install the required packages with `pip install -r requirements.txt`
3. Create a config.json file (you can just rename the example to config.json)
4. Create a servers.json file (you will need to put your own servers in this file, the example file is example only)
5. Create a discord bot token and add it to `.env` as `DISCORD_TOKEN=<token>`.
6. Add your discord bot to your discord server
7. Run the bot with `screen -mS startbot python3 bot.py`


## Usage

Commands:
- !help - Displays this help
- !botstop - Stops the bot
- !command [command] - Sends a command to the currently running server
- !forcestopserver - Forcibly stops the currently running server by sending keyboard interrupt
- !list - Lists currently running server and available servers
- !startserver [server name] - Starts a server
- !stopserver - Stops the currently running server
- !ping - Pings the bot

**NOTE:**
The bot allows running arbitrary scripts defined in the json file, and arbitrary commands if a discord user has the admin role and one of the startserver scripts opens a shell. This program is a proof of concept personal tool, and is not designed for robustness or security. Use it at your own risk, and make sure you understand the security implications if you decide to use it for more than basic testing. I do not accept any liablilty for any damage caused by the use of this program.

## Configuration

#### The bot requires a .env file (or equivalent) to access the discord bot token.

`BOT_TOKEN=<token>`

#### The config.json file contains the following keys:

- chat_channel: The discord channel to send messages to
- command_channel: The discord channel to send commands to
- command_prefix: The prefix for commands
- regex: A list of regular expressions to match server output
    - match: The regular expression to match
    - fstring: The format string to use for the message ({groups} will be replaced with the groups from the regex match)

#### The servers.json file contains the following keys for each server:

- path: The path to the server folder
- servername: The name of the server (used to start the server via Discord)
- command: The command to start the server

## TODO

- [x] Add currently running server variable
- [x] Add running server check to prevent multiple servers running
- [x] Add list command to see currently running servers
- [x] Add server stop command
- [x] Add server command command
- [x] Add server message passthrough
- [x] Add help command
- [x] Add discord message passthrough