import os

server_functions_path = os.getcwd()
bot_token_file = '/home/slime/mc_bot_token.txt'
new_server_url = 'https://www.minecraft.net/en-us/download/server'

# ========== Interfacing Options

# Local file access allows for server files/folders manipulation for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True

# Run Minecraft server using subprocess.Popen(). Note, If script halts the server will halt also. Useful if you can't get Tmux, but I recommend Tmux if you can.
# If use_tmux is also True, script will prioritize use_subprocess. Which means if both vars are True, MC server will run as subprocess instead of running in separate Tmux pane.
# And if use_rcon is also True, RCON capabilities will have top priority over Popen() and Tmux.
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

# ========== Misc

bot_log_file = f"{server_functions_path}/bot_log.txt"

mc_active_status = False
mc_subprocess = None

mc_auto_saveall = False
mc_auto_saveall_interval = 30

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

if use_rcon: import mctools, re
if server_files_access: import shutil, fileinput, json
