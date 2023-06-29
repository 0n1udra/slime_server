import discord, getpass, os
from os.path import join

# ========== Don't need to edit.
home_dir = os.path.expanduser('~')
# Needs user's name for setting directory paths
user = ''
try: user = os.getlogin()
except: user = getpass.getuser()
if not user: print("ERROR: Need to set 'user' variable in slime_vars.py")


# ========== Edit configuration here.
# Set as None if not using a python virtual env.
pyenv_activate_command = f'source /home/{user}/pyenvs/discord2/bin/activate'

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
# The command to use in server to use to check status. send_command() will send something like 'xp 0.64356...'.
status_checker_command = 'xp '

# Max number of log lines to read. Increase if server is really busy.
log_lines_limit = 500

# Wait time (in seconds) between sending command to MC server and reading server logs for output.
# Time between receiving command and logging output varies depending on PC specs, MC server type (papermc, vanilla, forge, etc), and how many mods.
command_buffer_time = 1

# Send 'save-all' to MC server every X minutes (default 60 minutes).
autosave_status = True
autosave_min_interval = 60

# For '?links' command. Shows helpful websites.
useful_websites = {'Minecraft Downlaod': 'https://www.minecraft.net/en-us/download',
                   'Forge Installer': 'https://files.minecraftforge.net/',
                   'CurseForge Download': 'https://curseforge.overwolf.com/',
                   'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                   'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                   'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                   }
