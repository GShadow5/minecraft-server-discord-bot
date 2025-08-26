# minecraft-server-discord-bot

A simple discord bot written in python for managing multiple minecraft servers through the same discord server. 

The bot can start a server and stop a server. It can also force stop a server if the server hangs. The list of servers the bot can manage is stored in a json file. See servers.json.example for an example of the json file. I want to support passing the minecraft chat through to discord, but I'm running into parsing errors with python's regex library. Passing discord chat through to minecraft does work.

### Installation

1. Clone the repository
2. Install the required packages with `pip install -r requirements.txt`
3. Create a config.json file (you can just rename the example to config.json)
4. Create a servers.json file (you will need to put your own servers in this file, the example file is example only)
5. Create a discord bot token and add it to `.env` as `DISCORD_TOKEN=<token>`.
6. Add your discord bot to your discord server
7. Run the bot with `screen -mS startbot python3 bot.py`


### Usage

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


### TODO

- [x] Add currently running server variable
- [x] Add running server check to prevent multiple servers running
- [x] Add list command to see currently running servers
- [x] Add server stop command
- [x] Add server command command
- [ ] Add server message passthrough
- [x] Add help command
- [x] Add discord message passthrough