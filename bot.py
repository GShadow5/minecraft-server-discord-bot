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
    if message.channel.name == chat_channel and not message.content.startswith(command_prefix):
        if not active_server:
            await ("No server is currently active.")
            return
        await send_message(message)
    if message.channel.name == command_channel and message.content.startswith(command_prefix):
        await bot.process_commands(message)

async def send_message(message):
    if not active_server:
        await message.channel.send("No server is currently active.")
        return
    minecraft_message = "[" + message.author.name + "] " + message.content
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff '{minecraft_message}\n'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
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
    global active_server
    active_server = servername

@bot.command()
async def stopserver(ctx, *args):
    # Check if the user is an admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    # Stop the server
    await ctx.send("Stopping server...")
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff 'stop\n'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    await ctx.send(stdout)
    await ctx.send("Server stopped.")
    global active_server
    active_server = None

@bot.command()
async def list(ctx):
    # Load server data from json
    servers = None
    with open('servers.json', 'r') as f:
        servers = json.load(f)
        servers = servers['servers']
    if servers is None:
        await ctx.send("No servers found in the servers.json file.")
        return
    
    # Get the currently running screens
    process = subprocess.Popen(f"screen -ls", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    # Get the currently active server
    currentservers = []
    for s in servers:
        if s['servername'] in stdout:
            currentservers.append(s)
    if len(currentservers) == 0:
        await ctx.send("No server is currently active.")
        active_server = None
    elif len(currentservers) > 1:
        await ctx.send("Multiple servers are currently active. This should not happen. Please report this to the server owner.")
        await ctx.send(f"Currently active servers: {', '.join([s['servername'] for s in currentservers])}")
        active_server = None
    else:
        await ctx.send(f"Server {currentservers[0]['servername']} is currently active.")
    if currentservers[0]['servername'] != active_server:
        active_server = currentservers[0]['servername']
    
    # List the available servers
    listofservers = f'Available servers: {"\n".join([s["servername"] for s in servers])}'
    await ctx.send(listofservers)

@bot.command()
async def forcestopserver(ctx, *args):
    # Check if the user is an admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    # Stop the server
    await ctx.send("Stopping server...")
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff $'\003'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff $'\003'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff $'\003'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    await ctx.send(stdout)
    await ctx.send("Server stopped.")
    global active_server
    active_server = None

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def botstop(ctx):
    await bot.close()

bot.run(TOKEN)