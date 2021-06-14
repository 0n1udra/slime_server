import os

bot_files_path = os.getcwd()
slime_vars_file = bot_files_path + '/slime_vars.py'
bot_token_file = '/home/slime/mc_bot.token'
new_server_url = 'https://www.minecraft.net/en-us/download/server'  # Where to get new server.jar for the update feature.

channel_id = None  # Optionally add channel ID, send message indicating bot is ready.

# ========== Interfacing Options
# Local file access allows for server files/folders manipulation,for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halts also. Useful if can't use Tmux.
# Prioritize use_subprocess over Tmux option.
use_subprocess = False

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True


# Use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
server_ip = ''  # Will be updated by get_server_ip function in server_functions.py on bot startup.
server_url = ''
rcon_pass = ''
rcon_port = 25575

# ========== Minecraft Server Config
# Location for Minecraft servers and backups, make sure is full path and is where you want it.
mc_path = '/mnt/c/Users/DT/Desktop/MC'

# Server profiles, allows you to have different servers and each with their own backups/restores.
# {'Server_Name': ['Server_name', 'Server_Description', 'Start_Command']}
server_list = {
    'papermc': ["papermc", 'Lightweight PaperMC.', f'java -Xmx3G -Xms1G -jar {mc_path}/papermc/server.jar nogui'],
    }

server_selected = server_list['papermc']
server_path = f"{mc_path}/{server_selected[0]}"
world_backups_path, server_backups_path = f"{mc_path}/world_backups/{server_selected[0]}", f"{mc_path}/server_backups/{server_selected[0]}"

# ========== Bot Config
# Default values.
autosave_status = True
autosave_interval = 60  # Minutes.

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

bot_log_file = f"{bot_files_path}/bot_log.txt"
mc_active_status = False  # If Minecraft server is running.
mc_subprocess = None  # If using subprocess, this is will be the Minecraft server.
log_lines_limit = 100  # Max number of log lines to read.

# For '?links' command. Shows helpful websites.
useful_websites = {
    'Forge Downnload (Download 35.1.13 Installer)': 'https://files.minecraftforge.net/',
    }

if use_rcon is True: import mctools, re
if server_files_access is True: import shutil, fileinput, json
