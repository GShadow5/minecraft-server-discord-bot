import os
import discord
from discord.ext import commands
import subprocess
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
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
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def botstop(ctx):
    await bot.close()


bot.run(TOKEN)