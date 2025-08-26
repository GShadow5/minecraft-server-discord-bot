import os

from dotenv import load_dotenv

from fsio import read_config_file, read_servers_file

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
BASE_PATH = os.getenv('BASE_PATH', './')

print(read_config_file("config.json")["chat_channel"])