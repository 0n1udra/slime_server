import time, sys, os
from discord_mc_bot import bot, TOKEN
from slime_vars import tmux_session_name
import server_functions

def setup_directories():
    """Create necessary directories."""

    try:
        # TODO Needed?
        # Creates Server folder, folder for world backups, and folder for server backups.
        os.makedirs(server_functions.server_path)
        print("Created:", server_functions.server_path)
        os.makedirs(server_functions.world_backups_path)
        print("Created:", server_functions.world_backups_path)
        os.makedirs(server_functions.server_backups_path)
        print("Created:", server_functions.server_backups_path)
    except:
        print("Error: Something went wrong setup up necessary directory structure at:", server_functions.server_path)

def start_tmux_session():
    """Starts Tmux session in detached mode, with 2 panes, and sets name."""

    try:
        os.system(f'tmux new -d -s {tmux_session_name}')
        print(f"Started Tmux detached session.")
    except: print(f"Error: Starting {tmux_session_name} detached session.")

    try:
        os.system(f'tmux split-window -v -t {tmux_session_name}:1.0')
        print("Created second tmux pane for Discord bot.")
    except: print("Error: Creating second tmux pane for Discord bot.")

    time.sleep(1)

def start_bot():
    if server_functions.use_tmux is True:
        os.system(f'tmux send-keys -t {tmux_session_name}:1.1 "cd {server_functions.bot_files_path}" ENTER')
        if not os.system(f"tmux send-keys -t {tmux_session_name}:1.1 'python3 discord_mc_bot.py' ENTER"):
            print(f"Started bot in {tmux_session_name} tmux session, top pane.")
            return True  # If os.system() return 0, means successful.
    else:
        print("Start server with ?start command in Discord.")
        input("Enter to exit > ")

def server_start():
    """Start Minecraft server, method varies depending on variables set in slime_vars.py."""

    if server_functions.use_tmux is True:
        server_functions.server_start()
    else: bot.run(TOKEN)

# TODO add update      - Downloads latest server.jar file from official Minecraft website to server folder.
def script_help():
    help = """
    python3 run_bot.py setup download startboth            --  Create required folders, downloads latest server.jar, and start server and bot with Tmux.
    python3 run_bot.py tmuxstart startboth tmuxattach      --  Start Tmux session, start server and bot, then attaches to Tmux session.
    
    help        - Shows this help page.
    setup       - Create necessary folders. Starts Tmux session in detached mode with 2 panes.
    starttmux   - Start Tmux session named with 2 panes. Top pane for Minecraft server, bottom for bot.
    startbot    - Start Discord bot.
    startserver - Start MC server.
    startboth   - Start Minecraft server and bot either using Tmux or in current console depending on corresponding variables.
    attachtmux  - Attaches to session. Will not start Tmux, use starttmux or setup.

    Note:   The corresponding functions will run in the order you pass arguments in.
            For example, 'python3 run_bot.py startbot tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
            Instead run 'python3 tmuxstart startboth tmuxattach', start Tmux session then start server and bot, then attach to Tmux session.
    """
    print(help)


if __name__ == '__main__':
    if 'setup' in sys.argv:
        if server_functions.server_files_access is True:
            setup_directories()
        if server_functions.use_tmux is True:
            start_tmux_session()
        if server_functions.use_rcon is True:
            print("Using RCON. Make sure relevant variables are set properly in server_functions.py.")

    if 'starttmux' in sys.argv and server_functions.use_tmux:
        start_tmux_session()
        time.sleep(1)

    if 'startbot' in sys.argv: start_bot()

    if 'startserver' in sys.argv: server_start()

    if 'startboth' in sys.argv:
        server_start()
        start_bot()

    if 'attachtmux' in sys.argv: os.system(f"tmux attach -t {tmux_session_name}")

    # My personal shortcut.
    if 'slime' in sys.argv:
        start_tmux_session()
        time.sleep(1)
        start_bot()
        os.system(f"tmux attach -t {tmux_session_name}")

    if 'help' in sys.argv: script_help()
