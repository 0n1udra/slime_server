import os, sys, time, server_functions
from discord_mc_bot import bot

disabled_commands = ['banlist', 'oplist', 'mootd', 'start', 'restart', 'saves', 'backup', 'restore', 'delete', 'newworld', 'properties', 'update',
                     'serversaves', 'serverbackup', 'serverdelete', 'serverrestore', 'serverreset', 'onlinemode', 'log']

# Exits script if no token.
if os.path.isfile(server_functions.discord_bot_token_file):
    with open(server_functions.discord_bot_token_file, 'r') as file:
        TOKEN = file.readline()
else: print("Missing Token File:", server_functions.discord_bot_token_file), exit()

def setup_directories():
    try:
        os.makedirs(server_functions.server_path)
        os.makedirs(server_functions.world_backups_path)
        os.makedirs(server_functions.server_backups_path)
    except: print("Error: Something went wrong setup up necessary directory structure.")

def start_tmux_session():
    try:
        os.system('tmux new -d -s mcserver')
        os.system('tmux send-keys -t mcserver:1.0 "tmux split-window -v" ENTER')
        time.sleep(1)
        os.system(f'tmux send-keys -t mcserver:1.1 "python3 {server_functions.discord_bot_file}" ENTER')
    except: server_functions.lprint("Error starting required detached tmux session with 2 windows with name: mcserver")

if server_functions.server_files_access is False:
    for command in disabled_commands:
        bot.remove_command(command)

if __name__ == '__main__':
    if 'setup' in sys.argv:
        server_functions.setup_directories()
        if server_functions.use_rcon:
            server_functions.start_tmux_session()
            server_functions.start_minecraft_server()
    else: bot.run(TOKEN)
