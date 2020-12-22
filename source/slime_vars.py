import os

server_functions_path = os.getcwd()
bot_token_file = '/home/slime/mc_bot_token.txt'
new_server_url = 'https://www.minecraft.net/en-us/download/server'

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
mc_ip = 'arcpy.asuscomm.com'
rcon_pass = 'SlimeySlime'
rcon_port = 25575

# ========== Minecraft Server Config

# This is where Minecraft server, world backups and server backups will be saved, so make sure this is a full path and is where you want it.
mc_path = '/mnt/c/Users/DT/Desktop/MC'

server_list = {'papermc': ["papermc", 'Lightweight PaperMC.', f'java -Xmx3G -Xms1G -jar {mc_path}/papermc/server.jar nogui' ],
               'vanilla': ["vanilla", 'Plain old vanilla.', f"java -Xmx3G -Xms1G -jar {mc_path}/vanilla/server.jar nogui",],
               'valhesia3': ["valhesia3", "140 mods!, Note: Takes a long time to start.", f"{mc_path}/valhesia3/ServerStart.sh"],
               }

server = server_list['papermc']
server_path = f"{mc_path}/{server[0]}"
world_backups_path = f"{mc_path}/world_backups/{server[0]}"
server_backups_path = f"{mc_path}/server_backups/{server[0]}"

# ========== Bot Config

bot_log_file = f"{server_functions_path}/bot_log.txt"

mc_active_status = False
mc_subprocess = None

# ===== Autosave
autosave = False
autosave_multiplier = 60  # 1: Seconds, 60: Minutes, 3_600: Hours
autosave_interval = autosave_multiplier * 30  # Default autosave value, e.g. 30m (30 * 3_600)

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

if use_rcon:
    import mctools, re
if server_files_access:
    import shutil, fileinput, json
