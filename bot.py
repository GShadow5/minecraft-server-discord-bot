import asyncio
import json
import os
import re
import discord
from discord.ext import commands
import subprocess
from dotenv import load_dotenv
import time

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
BASE_PATH = os.getenv('BASE_PATH', './')

chat_channel = None
command_channel = None
command_prefix = None
regex_list = []
fprint_list = []
with open('config.json', 'r') as f:
    config = json.load(f)
    chat_channel = config['config']['chat_channel']
    command_channel = config['config']['command_channel']
    command_prefix = config['config']['command_prefix']
    for regex in config['config']['regex']:
        regex_list.append(re.compile(regex['match']))
        fprint_list.append(regex['capture'])

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

active_server = None
active_server_pipe_task = None # To hold the asyncio task that reads from the pipe



'''



        # --- Named Pipe Functions ---


        
'''

def _get_pipe_path(servername):
    """Generates a consistent path for the named pipe."""
    return f"/tmp/minecraft_server_{servername}_pipe"

async def _create_named_pipe(servername):
    """
    Creates a named pipe (FIFO) for server output.
    """
    pipe_path = _get_pipe_path(servername)
    if os.path.exists(pipe_path):
        os.remove(pipe_path) # Ensure a clean pipe
    try:
        os.mkfifo(pipe_path)
        print(f"Named pipe created at: {pipe_path}")
    except OSError as e:
        print(f"Error creating named pipe {pipe_path}: {e}")
        raise

async def _delete_named_pipe(servername):
    """
    Deletes the named pipe (FIFO) file.
    """
    pipe_path = _get_pipe_path(servername)
    if os.path.exists(pipe_path):
        try:
            os.remove(pipe_path)
            print(f"Named pipe deleted: {pipe_path}")
        except OSError as e:
            print(f"Error deleting named pipe {pipe_path}: {e}")

# --- Pipe Reading and Parsing Task ---

async def _read_from_pipe(servername, channel_id, bot_instance):
    """
    Asynchronously reads from the named pipe, parses Minecraft output,
    and sends chat messages to the specified Discord channel.
    This function runs in its own asyncio task.
    """
    pipe_path = _get_pipe_path(servername)
    channel = bot_instance.get_channel(channel_id)
    if not channel:
        print(f"Error: Discord channel with ID {channel_id} not found.")
        return
    print(f"Sending to channel {channel_id}")

    print(f"Attempting to open named pipe for reading: {pipe_path}")
    try:
        # Open the pipe in non-blocking mode if possible, but for continuous
        # read, a blocking open in an executor thread is usually safer to
        # prevent CPU spin. Here we simulate that by using asyncio.to_thread
        # for the blocking 'open'.
        # However, for continuous reading from a pipe, the most common pattern
        # is to open it and read line-by-line in a loop.
        # We'll use 'open' directly as the stream will block until data is available.

        # The pipe will block until the server starts writing.
        # We need to run the blocking file operation in a separate thread
        # to avoid blocking the Discord bot's event loop.
        def _blocking_pipe_reader():
            with open(pipe_path, 'r', encoding='utf-8') as pipe_file:
                for line in pipe_file:
                    # Return line for processing in the async context
                    # Or process here and use queue for async sender
                    yield line
        
        # This will iterate over the generator from a separate thread
        # and yield lines back to the async context.
        # This is a bit advanced; a simpler approach often involves a queue.
        # For direct line-by-line, we'll simplify and acknowledge potential blocking
        # if the pipe is closed unexpectedly, but it's fine for our use case.
        # A more robust approach might use a queue and a dedicated thread for
        # the blocking read, with the async task consuming from the queue.

        # Simplified for direct demonstration, assuming graceful pipe closure:
        # Open the pipe with `os.open` and `os.read` to get more control for async,
        # or use `open` with a separate thread for the blocking read.
        # For simplicity and common patterns, we'll rely on `asyncio.to_thread` for `open` and `readline`.

        # We'll use a queue and a separate thread to handle the blocking read
        # to ensure the main asyncio loop remains responsive.
        line_queue = asyncio.Queue()

        def blocking_read_thread():
            try:
                # Open the pipe in blocking mode. This 'open' will block until a writer opens the pipe.
                with open(pipe_path, 'r', encoding='utf-8') as f:
                    print(f"Successfully opened pipe {pipe_path} for reading.")
                    while True:
                        line = f.readline() # This blocks until a line is available or pipe is closed
                        if not line: # EOF - pipe closed by writer
                            print(f"Pipe {pipe_path} closed by writer.")
                            break
                        line_queue.put_nowait(line) # Put line into the async queue
            except FileNotFoundError:
                print(f"Pipe {pipe_path} not found during read attempt (likely cleaned up).")
            except Exception as e:
                print(f"Error in blocking_read_thread for {pipe_path}: {e}")
            finally:
                # Signal the async reader that no more lines will come
                line_queue.put_nowait(None) # Sentinel value
                print(f"Blocking read thread for {pipe_path} finished.")


        # Start the blocking read in a separate thread
        loop = asyncio.get_event_loop()
        blocking_thread_task = loop.run_in_executor(None, blocking_read_thread)

        print(f"Starting async pipe reader for {servername}...")
        while True:
            line = await line_queue.get()
            if line is None: # Sentinel value received, pipe closed
                break
            
            line = line.strip()
            if not line:
                continue

            # print(f"Raw server output: {line}") # Debugging raw output
            global regex_list
            global fprint_list
            for i in range(len(regex_list)):
                match = regex_list[i].match(line)
                if match:
                    groups = match.groups()
                    discord_message = fprint_list[i].format(groups=groups)
                    # Limit message length for Discord if necessary
                    if len(discord_message) > 2000:
                        discord_message = discord_message[:1997] + "..."
                    print(discord_message)
                    await bot.loop.create_task(channel.send("Message sending..."))
                    await bot.loop.create_task(channel.send(discord_message))
                # else:
                #     # Optionally, you can log other server output to a debug channel or console
                #     print(f"Non-chat output: {line}")

            await asyncio.sleep(0.01) # Small delay to yield control and avoid busy-waiting

    except asyncio.CancelledError:
        print(f"Pipe reading task for {servername} was cancelled.")
    except Exception as e:
        print(f"Unhandled error in _read_from_pipe for {servername}: {e}")
    finally:
        print(f"Pipe reader for {servername} cleaning up.")
        # Ensure the blocking thread has a chance to finish or be stopped
        # If the pipe is forcefully deleted, the blocking read will raise FileNotFoundError.
        # If the server closes the write end, the blocking read will return empty strings.
        # This cleanup should happen after the server is truly stopped and the pipe is deleted.
        # We will handle pipe deletion separately in stop/forcestop.


async def _stop_server_internal(ctx, servername, method):
    '''
    Internal helper to stop a server and clean up.
    '''
    global active_server, active_server_pipe_task

    if not ctx.author.guild_permissions.administrator and method == "forcestop":
        await ctx.send("You don't have permission to run this command.")
        return
    
    if active_server is None or active_server != servername:
        await ctx.send(f"No server '{servername}' is currently active, or a different server is running.")
        return

    await ctx.send(f"Attempting to {method} server '{servername}'...")

    if method == "stop":
        command_to_send = 'stop\n'
    elif method == "forcestop":
        command_to_send = "$'\003'" # Ctrl+C
    else:
        await ctx.send("Invalid stop method.")
        return

    # Send the stop command to the screen session
    screen_cmd = f"screen -S {servername} -X stuff '{command_to_send}'"
    print(f"Sending stop command to screen: {screen_cmd}")
    try:
        subprocess.Popen(screen_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        await ctx.send(f"Failed to send stop command to screen: {e}")
        # Even if command fails, attempt cleanup
    
    # Give the server some time to shut down gracefully
    if method == "stop":
        await asyncio.sleep(15) # Minecraft servers can take a while to save and stop
    else: # forcestop
        await asyncio.sleep(5) # Give it a few seconds for Ctrl+C to register

    # --- Cleanup ---
    if active_server_pipe_task:
        active_server_pipe_task.cancel()
        try:
            await active_server_pipe_task # Await to ensure it cleans up
        except asyncio.CancelledError:
            pass # Expected
        active_server_pipe_task = None

    await _delete_named_pipe(servername) # Delete the pipe file

    # Verify screen session is gone (optional, but good for robust cleanup)
    check_screen_cmd = f"screen -ls | grep {servername}"
    process = subprocess.Popen(check_screen_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    if not stdout:
        await ctx.send(f"Server `{servername}` successfully {method}ped and screen session terminated.")
    else:
        await ctx.send(f"Server `{servername}` {method}ped, but screen session still detected. Manual intervention might be needed.")
        print(f"Remaining screen -ls output for {servername}:\n{stdout}")

    active_server = None # Clear active server state

async def connect_to_existing_pipe():
    global active_server, active_server_pipe_task, chat_channel, bot
    # Get list of servers
    with open('servers.json', 'r') as f:
        servers = json.load(f)
        servers = servers['servers']
    
    # Get list of active screens
    screen_cmd = "screen -ls"
    process = subprocess.Popen(screen_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    # Check for existing pipes
    for server in servers:
        if server['servername'] in stdout:
            active_server = server['servername']
            if os.path.exists(_get_pipe_path(active_server)):
                await _read_from_pipe(active_server, chat_channel, bot)
                return

'''




    Handle events (messages mostly)




'''
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user})')
    await connect_to_existing_pipe()

@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
    if message.author == bot.user:
        return
    if message.channel.name == chat_channel and not message.content.startswith(command_prefix):
        if not active_server:
            await message.channel.send("No server is currently active.")
            return
        await send_message(message)
    if message.channel.name == command_channel and message.content.startswith(command_prefix):
        await bot.process_commands(message)

async def send_message(message):
    global active_server
    if not active_server:
        await message.channel.send("No server is currently active.")
        return
    minecraft_message = "[" + message.author.name + "] " + message.content
    process = subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff 'say {minecraft_message}\n'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()





'''




    Handle commands




'''
@bot.command()
async def startserver(ctx, *args):
    '''
    Start a server
    args:
        servername: The name of the server

    '''
    global active_server, active_server_pipe_task
    # Validate and get the server name
    if len(args) != 1:
        await ctx.send("Please provide exactly one server name.")
        return
    servername = args[0]

    # Check if the server is already running
    if active_server is not None:
        await ctx.send("A server is already running, please stop it first. If you think this is an error, run !list to refresh the list of servers and try again.")
        return

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

    # Create the named pipe
    try:
        await _create_named_pipe(servername)
    except Exception as e:
        await ctx.send(f"Failed to create named pipe: {e}")
        return

    # Create the paths
    pipe_path = _get_pipe_path(servername)
    path = os.path.join(BASE_PATH, server['path']) if BASE_PATH else server['path']

    # Check if the server path exists
    if not os.path.isdir(path):
        await ctx.send("Server path does not exist.")
        await _delete_named_pipe(servername)
        return

    screen_cmd = (
        f"cd {path} && "
        f"screen -dmS {servername} bash -c \"{server['startcommand']} | tee {pipe_path}\""
    )

    #command = f"cd {path} && screen -dmS {servername} {server['startcommand']}"
    #print(f"Running command: {command}")
    print(f"Running screen command: {screen_cmd}")
    try:
        subprocess.Popen(screen_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except Exception as e:
        await ctx.send(f"Failed to start server: {e}")
        await _delete_named_pipe(servername)
        return
    
    # Wait for the server to start then check if the screen instance is still live
    await asyncio.sleep(2)
    process = subprocess.Popen(f"screen -ls | grep {servername}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    if not stdout:
        await ctx.send("Server failed to start. Minecraft screen instance terminated within 3 seconds.")
        await _delete_named_pipe(servername)
        return

    await ctx.send(f'Started server in screen session: {servername}')
    print(f'Started server in screen session: {servername}')
    print(f'stdout: {stdout}')

    active_server = servername

    # Start reading from the pipe
    active_server_pipe_task = asyncio.create_task(_read_from_pipe(servername, ctx.channel.id, ctx.bot))
    await ctx.send(f'Now monitoring output from `{servername}` in this channel.')

@bot.command()
async def stopserver(ctx):
    '''
    Stop the server by sending 'stop' to the server

    '''
    global active_server
    if active_server is None:
        await ctx.send("No server is currently active.")
        return
    await _stop_server_internal(ctx, active_server, "stop")

@bot.command()
async def command(ctx, *args):
    '''
    Send a command to the server
    args:
        command: The command to send

    '''
    global active_server
    # Check if the user is an admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    # Send the command to the server
    await ctx.send("Sending command...")
    command = " ".join(args)
    subprocess.Popen(f"screen -S {active_server} -p 0 -X stuff '{command}\n'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

@bot.command()
async def list(ctx):
    '''
    Lists currently running server and available servers

    '''
    global active_server
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
    if len(currentservers) > 0 and currentservers[0]['servername'] != active_server:
        active_server = currentservers[0]['servername']
    
    # List the available servers
    listofservers = 'Available servers: '+ "\n".join([s["servername"] for s in servers])
    await ctx.send(listofservers)

@bot.command()
async def forcestopserver(ctx):
    '''
    Force stop the server by sending keyboard interrupt

    '''
    global active_server
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    if active_server is None:
        await ctx.send("No server is currently active.")
        return
    await _stop_server_internal(ctx, active_server, "forcestop")

@bot.command()
async def reloadregex(ctx):
    '''
    Reload the regex for the server

    '''
    global regex_list, fprint_list
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to run this command.")
        return
    regex_list = []
    fprint_list = []
    with open('config.json', 'r') as f:
        config = json.load(f)
        for regex in config['config']['regex']:
            regex_list.append(re.compile(regex['match']))
            fprint_list.append(regex['capture'])
    await ctx.send("Regex reloaded.")

@bot.command()
async def ping(ctx):
    '''
    Ping the bot

    '''
    await ctx.send('Pong!')

@bot.command()
async def botstop(ctx):
    '''
    Stop the bot and clean up
    '''
    global active_server, active_server_pipe_task

    if active_server is not None:
        await ctx.send(f"Server running, please stop the server before stopping the bot.")
        return
    
    await bot.close()
    print("Bot stopped.")

bot.run(TOKEN)
