import json
import os
import discord
from discord.ext import commands
import subprocess
from dotenv import load_dotenv
import time

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
BASE_PATH = os.getenv('BASE_PATH', './')
print(TOKEN)

chat_channel = None
command_channel = None
command_prefix = None
with open('config.json', 'r') as f:
    config = json.load(f)
    chat_channel = config['config']['chat_channel']
    command_channel = config['config']['command_channel']
    command_prefix = config['config']['command_prefix']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

active_server = None

'''
    Handle events (messages mostly)
'''
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user})')

@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
    if message.author == bot.user:
        return
    if message.channel.name == chat_channel:
        if not active_server:
            await ("No server is currently active.")
            return
        await send_message(message)
    await bot.process_commands(message)

async def send_message(message):
    if not active_server:
        await message.channel.send("No server is currently active.")
        return
    minecraft_message = "[" + message.author.name + "] " + message.content
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff '{minecraft_message}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

'''
    Handle commands
'''
@bot.command()
async def startserver(ctx, *args):
    # Check if the user is an admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    # Validate and get the server name
    if len(args) == 0:
        await ctx.send("Please provide a server name.")
        return
    if len(args) > 1:
        await ctx.send("Please provide only one server name.")
        return
    servername = args[0]

    # Load server data from json
    with open('servers.json', 'r') as f:
        servers = json.load(f)
        servers = servers['servers']
    # Find the server in the json
    server = None
    for s in servers:
        if s['servername'] == servername:
            server = s
            break
    if server is None:
        await ctx.send("Server not found.")
        return
    # Start the server
    await ctx.send("Starting server, please wait...")
    path = BASE_PATH + server['path'] if BASE_PATH else server['path']
    command = f"cd {path} && screen -dmS {servername} {server['startcommand']}"
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Wait for the server to start then check if the screen instance is still live
    stdout, stderr = process.communicate()
    time.sleep(3)
    process = subprocess.Popen(f"screen -ls | grep {servername}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    print(stdout)
    if len(stdout) == 0:
        await ctx.send("Server failed to start. Minecraft screen instance terminated within 3 seconds.")
        return
    await ctx.send("Server started.")
    await ctx.send(stdout)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def botstop(ctx):
    await bot.close()

bot.run(TOKEN)