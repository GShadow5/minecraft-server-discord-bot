import json

def read_config_file(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config['config']

def read_servers_file(servers_file):
    with open(servers_file, 'r') as f:
        servers = json.load(f)
    return servers['servers']