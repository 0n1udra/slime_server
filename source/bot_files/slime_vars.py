import discord, getpass, platform, csv, os
from os.path import join

# ========== Don't need to edit.
__version__ = "7.2"
__date__ = '29/06/2023'
__author__ = "github.com/0n1udra"
__license__ = "GPL 3"
__status__ = "Development"
home_dir = os.path.expanduser('~')

# ========== Edit configuration here.
# ===== Discord
# Set location of Discord bot token using os.path.join. e.g. join(home_dir, 'keys', 'slime_bot.token')
bot_token_file = join(home_dir, 'keys', 'slime_bot.token')
command_prefex = '?'
case_insensitive = True  # Case insensitivy for discord commands. e.g. ?players, ?Players, ?pLaYers
# Discord Developer Portal > Applications > Your bot > Bot > Enable 'MESSAGE CONTENT INTENT' Under 'Privileged Gateway Intents'
intents = discord.Intents.default()
intents.message_content = True

# Optionally add channel ID, send message indicating bot is ready on startup.
channel_id = None  # Default: None

# ===== Minecraft Interfacing Options
# Server URL or IP address. Used for server_ping(), ping_url(), etc, .
server_address = ''
server_port = 25565

# Local file access allows for server files/folders manipulation,for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Use screen to start and send commands to Minecraft server. Only Minecraft server, bot can be run alone or in tmux.
server_use_screen = False
screen_session_name = 'server'  # Make sure your screen session is named if starting server outside of bot.

# Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halt also. Useful if can't use Tmux.
use_subprocess = False  # Prioritizes use_subprocess over Tmux option.

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True
tmux_session_name = 'sess'
tmux_bot_pane = '0.0'  # tmux pane for slime_bot. Default: 0.0
tmux_minecraft_pane = '0.1'  # tmux pane for Miencraft server. Default: 0.1

# Use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
rcon_pass = ''
rcon_port = 25575

# Location for Minecraft servers and backups, make sure is full path and is where you want it.
# Use os.path.join. e.g. join(home_dir, 'Games', 'Minecraft) is ~/Games/Minecraft/
mc_path = join(home_dir, 'Games', 'Minecraft')

# Second to wait before checking status for ?serverstart. e.g. PaperMC ~10s (w/ decent hardware), Vanilla ~20, Valhesia Volatile ~40-50s.
default_wait_time = 30

# Default server launch command to start Minecraft java server.
server_launch_command = 'java -server -Xmx4G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2 -jar server.jar nogui'

# ===== Bot Config
# This command sent to server to check if responsive. send_command() will send something like 'xp 0.64356...'.
status_checker_command = 'xp '
# Set to False to disable sending 'xp' command to server. NOTE: You won't get for some commands you won't get feedback on success/status.
enable_status_checker = True

# Max number of log lines to read. Increase if server is really busy.
log_lines_limit = 500

# Wait time (in seconds) between sending command to MC server and reading server logs for output.
# Time between receiving command and logging output varies depending on PC specs, MC server type (papermc, vanilla, forge, etc), and how many mods.
command_buffer_time = 1

# Send 'save-all' to MC server every X minutes (default 60 minutes).
autosave_status = True
autosave_min_interval = 60

# Can clear all this and set pyenv command manually -----
user = ''
try: user = os.getlogin()
except: user = getpass.getuser()
if not user: print("ERROR: Need to set 'user' variable in slime_vars.py")
# -------------------------------------------------------
# Set as None if not using a python virtual env.
pyenv_activate_command = f'source /home/{user}/pyenvs/discord2/bin/activate'

# Get the operating system. Makes server launch command compataible with windows CMD.
windows_cmdline_start = False
if platform.system() == 'Windows':
    on_windows = True
    windows_cmdline_start = 'start "Minecraft server"'  # Will be prefixed to server_launch_command in server_start() func to be windows compatible.

# For '?links' command. Shows helpful websites.
useful_websites = {'Minecraft Downlaod': 'https://www.minecraft.net/en-us/download',
                   'Forge Installer': 'https://files.minecraftforge.net/',
                   'CurseForge Download': 'https://curseforge.overwolf.com/',
                   'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                   'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                   'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                   }

# ========== Other Games
steam_path = f'/home/{user}/.steam/steam/steamapps/common'

# ========== Don't need to edit.

# Create servers.csv file if not exist.
# Server profiles, allows you to have different servers and each with their own backups/restores.
# {'server_name': ['server_name', 'description', 'start_Command', optional_startup_wait_time]}
# No spaces allowed in server name. Always put optional_wait_time at tail of list.
servers = {'example': ['example', 'Description of server', server_launch_command, 30]}
# TODO add to csv if foler exist
with open(join('bot_files', 'servers.csv'), "a") as f: pass  # Create file if not exist.
# Add servers from csv file.
with open(join('bot_files', 'servers.csv'), 'r') as f:
    csv_data = csv.reader(f, skipinitialspace=True)
    for i in csv_data:
        if not i: continue
        if 'Example Entry' == i[0]: continue
        i[2] = i[2].replace('PARAMS', server_launch_command)  # Replaces 'PARAMS' with server_launch_command string.
        servers[i[0]] = i
_server_selected = 'papermc'
if _server_selected in servers.keys():
    server_selected = servers[_server_selected]
else: server_selected = servers['example']
servers_path = join(mc_path, 'servers')  # Path to all servers
server_path = join(servers_path, server_selected[0])  # Path to currently selected server
world_backups_path = join(mc_path, 'world_backups', server_selected[0])
server_backups_path = join(mc_path, 'server_backups', server_selected[0])
server_log_path = join(server_path, 'logs')
server_log_file = join(server_log_path, 'latest.log')

exact_foldername = False  # Set to True to backup 'world' folder only.
server_ip = server_address  # Will be updated by get_ip() function in backend_functions.py on bot startup.
mc_active_status = False  # If Minecraft server is running.
mc_subprocess = None  # If using subprocess, this will be the Minecraft server.

if use_rcon is True: import mctools, re
if server_files_access is True: import shutil, fileinput, json
if not server_address: server_address = 'N/A'

# Disable certain commands depending on if have local server file access.
if_no_file_access = ['serverstart', 'serverrestart', 'autosaveon', 'autosaveoff', 'chatlog',
                     'motd', 'oplist', 'properties', 'propertiesall', 'rcon', 'onlinemode', 'serverconnections',
                     'restoreworldpanel', 'worldbackupslist', 'worldbackupnew', 'worldbackupdate', 'worldbackuprestore', 'worldbackupdelete', 'worldreset',
                     'restoreserverpanel', 'serverbackupslist', 'serverbackupnew', 'serverbackupdate', 'serverbackupdelete', 'serverbackuprestore', 'serverreset', 'serverupdate', 'serverlog'
                     ]

if server_files_access: if_no_file_access = []

# Import user's configs
try: from user_config import *
except: pass

bot_src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
user_config_file = join(bot_src_path, 'user_config.py')
slime_vars_file = join(bot_src_path, 'bot_files', 'slime_vars.py')
bot_files_path = join(bot_src_path, 'bot_files')
bot_log_file = join(bot_src_path, 'slime_bot.log')
