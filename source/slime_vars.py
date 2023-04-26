import discord, platform, os
from os.path import join

home_dir = os.path.expanduser('~')

use_cmdline_start = False
# Get the operating system name
if platform.system() == 'Windows':
    on_windows = True
    use_cmdline_start = True  # Enable to use the 'start' command in windows cmd to start java server.

try: user = os.getlogin()
except:
    import getpass
    user = getpass.getuser()
if not user: print("ERROR: Need to set 'user' variable in slime_vars.py")

# Set as None if not using a python virtual env.
pyenv_activate_command = f'source /home/{user}/pyenvs/discord2/bin/activate'

# ========== Discord
# Set location of Discord bot token using os.path.join. e.g. join(home_dir, 'keys', 'slime_bot.token')
bot_token_file = join(home_dir, 'keys', 'slime_bot.token')
command_prefex = '?'
case_insensitive = True  # Case insensitivy for discord commands. e.g. ?players, ?Players, ?pLaYers
# Discord Developer Portal > Applications > Your bot > Bot > Enable 'MESSAGE CONTENT INTENT' Under 'Privileged Gateway Intents'
intents = discord.Intents.default()
intents.message_content = True

# Optionally add channel ID, send message indicating bot is ready on startup.
channel_id = 860361620492255292  # Default: None

# ========== Other Games
steam_path = f'/home/{user}/.steam/steam/steamapps/common'

# ========== Minecraft Interfacing Options
# Server URL or IP address. Used for server_ping(), ping_url(), etc, .
server_url = ''
server_port = 25565

# Local file access allows for server files/folders manipulation,for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True

# Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halts also. Useful if can't use Tmux.
use_subprocess = False  # Prioritizes use_subprocess over Tmux option.

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True
tmux_session_name = 'sess'
tmux_bot_pane = '0.0'  # tmux pane for slime_bot
tmux_minecraft_pane = '0.1'  # tmux pane for miencraft server

# Use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
rcon_pass = ''
rcon_port = 25575

# ========== Minecraft Server Config
# Location for Minecraft servers and backups, make sure is full path and is where you want it.
# Use os.path.join. e.g. join(home_dir, 'Games', 'Minecraft) is ~/Games/Minecraft/
mc_path = join(home_dir, 'Games', 'Minecraft')

# Second to wait before checking status for ?serverstart. e.g. PaperMC ~10s (w/ decent hardware), Vanilla ~20, Valhesia Volatile ~40-50s.
default_wait_time = 30

# Server profiles, allows you to have different servers and each with their own backups/restores.
# {'server_name': ['server_name', 'description', 'start_Command', 'optional_jar_download_url', optional_wait_time]}
# No spaces allowed in server name. Always put optional_wait_time at tail of list.
# Note: the URL is just for show, the bot uses corresponding API to check and download latest server jar file.
java_params = '-server -Xmx4G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2'

# Do not edit these lines.
servers = {'example': ['Example Entry', 'Description of server', f'java {java_params} server.jar nogui' , 30]}
server_selected = servers['papermc']  # Currently selected server
servers_path = join(mc_path, 'servers')  # Path to all servers
server_path = join(servers_path, server_selected[0])  # Path to currently selected server
world_backups_path = join(mc_path, 'world_backups', server_selected[0])
server_backups_path = join(mc_path, 'server_backups', server_selected[0])
server_log_path = join(server_path, 'logs')
server_log_file = join(server_log_path, 'latest.log')

# ========== Bot Config
bot_src_path = os.path.dirname(os.path.abspath(__file__))
bot_files_path = join(bot_src_path, 'bot_files')
slime_vars_file = join(bot_src_path, 'slime_vars.py')
bot_log_file = join(bot_src_path, 'slime_bot.log')

# The command to use in server to use to check status. send_command() will send something like 'xp 0.64356...'.
status_checker_command = 'xp '

# Max number of log lines to read. Increase if server is really busy (has a lot ouf console logging)
log_lines_limit = 500

# Wait time (in seconds) between sending command to MC server and reading server logs for output.
# Time between receiving command and logging output varies depending on PC specs, MC server type (papermc, vanilla, forge, etc), and how many mods.
command_buffer_time = 1

# Autosave functionality. interval is in minutes.
autosave_status = True
autosave_interval = 60

mc_active_status = False  # If Minecraft server is running.
mc_subprocess = None  # If using subprocess, this is will be the Minecraft server.

# For '?links' command. Shows helpful websites.
useful_websites = {'Minecraft Downlaod': 'https://www.minecraft.net/en-us/download',
                   'Forge Installer': 'https://files.minecraftforge.net/',
                   'CurseForge Download': 'https://curseforge.overwolf.com/',
                   'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                   'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                   'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                   }

# ========== Misc
server_ip = server_url  # Will be updated by get_ip() function in backend_functions.py on bot startup.

if use_rcon is True: import mctools, re
if server_files_access is True: import shutil, fileinput, json
