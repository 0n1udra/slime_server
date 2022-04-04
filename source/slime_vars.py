import os


# Set this variable if you're also using Debian based system. if not ignore this and manually set your file/folder paths.
user = '0n1udra'

# Set location of Discord bot token.
bot_token_file = f'/home/{user}/keys/slime_server.token'

# Set as None if not using a python virtual env.
pyenv_activate_command = f'source /home/{user}/pyenvs/slime_server/bin/activate'

# Optionally add channel ID, send message indicating bot is ready on startup.
channel_id = 860361620492255292

# Server URL or IP address. In case you're using a DDNS or something.
server_url = 'arcpy.asuscomm.com'

# ========== Interfacing Options
# Local file access allows for server files/folders manipulation,for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halts also. Useful if can't use Tmux.
# Prioritize use_subprocess over Tmux option.
use_subprocess = False

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True
tmux_session_name = 'sess'

# Use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
rcon_pass = 'rconpass420'
rcon_port = 25575

# ========== Minecraft Server Config
# Location for Minecraft servers and backups, make sure is full path and is where you want it.
mc_path = f'/home/{user}/Games/Minecraft'

# Server profiles, allows you to have different servers and each with their own backups/restores.
# {'Server_Name': ['name', 'description', 'start_Command', 'jar_download_url']}
# Note: the URL is just for show, the bot uses corresponding API to check and download latest server jar file.
java_params = '-server -Xmx2G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2'
server_list = {'papermc': ["papermc", 'Lightweight PaperMC.', f'java {java_params} -jar {mc_path}/papermc/server.jar nogui', 'https://papermc.io/downloads'],
               'vanilla': ["vanilla", 'Plain old vanilla.', f"java {java_params} -jar {mc_path}/vanilla/server.jar nogui", 'https://www.minecraft.net/en-us/download/server'],
               'valhesia3': ["valhesia3", "140 mods!, Note: Takes a long time to start.", f"java -jar -Xms3G -Xmx6G -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions -XX:MaxGCPauseMillis=100 -XX:+DisableExplicitGC -XX:TargetSurvivorRatio=90 -XX:G1NewSizePercent=50 -XX:G1MaxNewSizePercent=80 -XX:G1MixedGCLiveThresholdPercent=50 -XX:+AlwaysPreTouch forge-1.16.4-35.1.13.jar nogui"],
               'ulibrary': ['ulibrary', 'The Uncensored Library.', f'java -Xmx3G -Xms1G -jar {mc_path}/ulibrary/server.jar nogui'],
               }

server_selected = server_list['papermc']
server_path = f"{mc_path}/{server_selected[0]}"
# Where to save world and server backups.
world_backups_path = f"{mc_path}/world_backups/{server_selected[0]}"
server_backups_path = f"{mc_path}/server_backups/{server_selected[0]}"

# ========== Bot Config
log_lines_limit = 100  # Max number of log lines to read.

# Autosave functionality. interval is in minutes.
autosave_status = False
autosave_interval = 60

mc_active_status = False  # If Minecraft server is running.
mc_subprocess = None  # If using subprocess, this is will be the Minecraft server.

# For '?links' command. Shows helpful websites.
useful_websites = {'Forge Downnload (Download 35.1.13 Installer)': 'https://files.minecraftforge.net/',
                   'CurseForge Download': 'https://curseforge.overwolf.com/',
                   'Valhesia 3.1': 'https://www.curseforge.com/minecraft/modpacks/valhelsia-3',
                   'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                   'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                   'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                   }

# ========== Other variables. DON'T TOUCH.
bot_files_path = os.getcwd()
slime_vars_file = bot_files_path + '/slime_vars.py'
bot_log_file = f"{bot_files_path}/bot_log.txt"
updatable_mc = ['vanilla', 'papermc']
server_ip = ''  # Will be updated by get_ip function in backend_functions.py on bot startup.

if use_rcon is True: import mctools, re
if server_files_access is True: import shutil, fileinput, json
