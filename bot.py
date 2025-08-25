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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user})')

@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
    await bot.process_commands(message)

@bot.command()
async def mc(ctx, *args):
    command = ' '.join(args)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    await ctx.send(stdout)

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