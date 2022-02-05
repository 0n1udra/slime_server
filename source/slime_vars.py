import os

# Other Games
pass_path, valheim_password = '/home/0n1udra/keys/valheim_password.txt', ''
if os.path.isfile(pass_path):
    with open(pass_path, 'r') as file:
        valheim_password = file.readline()
valheim_path = '/home/0n1udra/Games/valheim'
valheim_log_path = '/home/0n1udra/Games/valheim/log/console/vhserver-console.log'


bot_token_file = '/home/0n1udra/keys/slime_server.token'  # Set location of Discord bot token.
pyenv_activate_command = 'source /home/0n1udra/pyenvs/slime_server/bin/activate'  # Set as None if not using a python virtual env.

bot_files_path = os.getcwd()
slime_vars_file = bot_files_path + '/slime_vars.py'
new_server_url = 'https://www.minecraft.net/en-us/download/server'  # Where to get new server.jar for the update feature.

# Optionally add channel ID, send message indicating bot is ready.
channel_id = 860361620492255292
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
server_ip = ''  # Will be updated by ip_ip function in backend_functions.py on bot startup.
server_url = 'arcpy.asuscomm.com'
rcon_pass = 'rconpass420'
rcon_port = 25575

# ========== Minecraft Server Config
# Location for Minecraft servers and backups, make sure is full path and is where you want it.
mc_path = '/home/0n1udra/Games/Minecraft'

# Server profiles, allows you to have different servers and each with their own backups/restores.
# {'Server_Name': ['Server_name', 'Server_Description', 'Start_Command']}
java_params = '-server -Xmx3G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2'
server_list = {'papermc': ["papermc", 'Lightweight PaperMC.', f'java {java_params} -jar {mc_path}/papermc/server.jar nogui'],
               'vanilla': ["vanilla", 'Plain old vanilla.', f"java {java_params} -jar {mc_path}/vanilla/server.jar nogui"],
               'valhesia3': ["valhesia3", "140 mods!, Note: Takes a long time to start.", f"java -jar -Xms3G -Xmx6G -XX:+UseG1GC -XX:+UnlockExperimentalVMOptions -XX:MaxGCPauseMillis=100 -XX:+DisableExplicitGC -XX:TargetSurvivorRatio=90 -XX:G1NewSizePercent=50 -XX:G1MaxNewSizePercent=80 -XX:G1MixedGCLiveThresholdPercent=50 -XX:+AlwaysPreTouch forge-1.16.4-35.1.13.jar nogui"],
               'ulibrary': ['ulibrary', 'The Uncensored Library.', f'java -Xmx3G -Xms1G -jar {mc_path}/ulibrary/server.jar nogui'],
               }

server_selected = server_list['papermc']
server_path = f"{mc_path}/{server_selected[0]}"
world_backups_path, server_backups_path = f"{mc_path}/world_backups/{server_selected[0]}", f"{mc_path}/server_backups/{server_selected[0]}"

# ========== Bot Config
# Default autosave values, interval is in minutes.
autosave_status = False
autosave_interval = 60

bot_log_file = f"{bot_files_path}/bot_log.txt"
mc_active_status = False  # If Minecraft server is running.
mc_subprocess = None  # If using subprocess, this is will be the Minecraft server.
log_lines_limit = 100  # Max number of log lines to read.

# For '?links' command. Shows helpful websites.
useful_websites = {'Forge Downnload (Download 35.1.13 Installer)': 'https://files.minecraftforge.net/',
                   'CurseForge Download': 'https://curseforge.overwolf.com/',
                   'Valhesia 3.1': 'https://www.curseforge.com/minecraft/modpacks/valhelsia-3',
                   'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                   'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                   'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                   }

if use_rcon is True: import mctools, re
if server_files_access is True: import shutil, fileinput, json
