import os

bot_files_path = os.getcwd()
slime_vars_file = bot_files_path + '/slime_vars.py'
bot_token_file = '/home/slime/mc_bot_token.txt'
new_server_url = 'https://www.minecraft.net/en-us/download/server'

channel_id = 754803768733728848  # Optionally add channel ID, so bot can send message when ready.

# ========== Interfacing Options

# Local file access allows for server files/folders manipulation for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True

# Uses subprocess.Popen(). If script halts, server halts also. Useful if not using Tmux, recommend using Tmux if can.
# Prioritize use_subprocess over Tmux option.
use_subprocess = False

# If you have local access to server files but not using Tmux, use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
server_ip = ''  # Will be updated by get_server_ip function in server_functions.py on bot startup.
server_url = 'arcpy.asuscomm.com'
rcon_pass = 'SlimeySlime'
rcon_port = 25575

# ========== Minecraft Server Config

# This is where Minecraft server, world backups and server backups will be saved, so make sure this is a full path and is where you want it.
mc_path = '/mnt/c/Users/DT/Desktop/MC'

# {'Server_Name': ['Server_name', 'Server_Description', 'Start_Command']}
server_list = {'papermc': ["papermc", 'Lightweight PaperMC.', f'java -Xmx3G -Xms1G -jar {mc_path}/papermc/server.jar nogui' ],
               'vanilla': ["vanilla", 'Plain old vanilla.', f"java -Xmx3G -Xms1G -jar {mc_path}/vanilla/server.jar nogui",],
               'valhesia3': ["valhesia3", "140 mods!, Note: Takes a long time to start.", f"{mc_path}/valhesia3/ServerStart.sh"],
               }

server_selected = server_list['papermc']
server_path = f"{mc_path}/{server_selected[0]}"

world_backups_path = f"{mc_path}/world_backups/{server_selected[0]}"
server_backups_path = f"{mc_path}/server_backups/{server_selected[0]}"

# ========== Bot Config

# Default values.
autosave_status = True
autosave_interval = 30

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

bot_log_file = f"{bot_files_path}/bot_log.txt"
mc_active_status = False
mc_subprocess = None

log_lines_limit = 100  # Limit how max number of log lines to read.

if use_rcon is True:
    import mctools, re
if server_files_access is True:
    import shutil, fileinput, json
