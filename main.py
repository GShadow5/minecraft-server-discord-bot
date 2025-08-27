# Base level imports
import os

# Third-party imports
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Local imports
from fsio import read_config_file, read_servers_file

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
BASE_PATH = os.getenv('BASE_PATH', './')

config = read_config_file("config.json")
servers = read_servers_file("servers.json")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config['command_prefix'], intents=intents)

'''
    Handle events
'''
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

'''
    Handle commands
'''
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')


bot.run(TOKEN)