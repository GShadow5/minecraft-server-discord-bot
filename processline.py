import discord
import re
import random

async def processline(line, regex_list, fprint_list, bot_instance, channel):
    for i in range(len(regex_list)):
        # print(f"Processing line: {line}")
        match = regex_list[i].match(line)
        if match:
            # print(f"Matched line: {line}")
            groups = match.groups()
            discord_message = fprint_list[i].format(groups=groups)
            # Limit message length for Discord if necessary
            if len(discord_message) > 2000:
                discord_message = discord_message[:1997] + "..."
            print(discord_message)
            await bot_instance.loop.create_task(channel.send(discord_message))
        # else:
        #     # Optionally, you can log other server output to a debug channel or console
        #     if random.random() < 0.01:
        #         print(f"Non-chat output: {line}")

def testreload():
    return "some new string"