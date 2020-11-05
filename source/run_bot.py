import time, sys, os
from discord_mc_bot import bot, TOKEN
import server_functions

__version__ = "3.1.1"
__author__ = "D Thomas"
__email__ = "dt01@pm.me"
__license__ = "GPL 3"
__status__ = "Development"

def setup_directories():
    try:
        os.makedirs(server_functions.server_path)
        print("Created:", server_functions.server_path)
        os.makedirs(server_functions.world_backups_path)
        print("Created:", server_functions.world_backups_path)
        os.makedirs(server_functions.server_backups_path)
        print("Created:", server_functions.server_backups_path)
    except: print("Error: Something went wrong setup up necessary directory structure at:", server_functions.server_path)

    try:
        with open(server_functions.bot_properties_file, 'w') as file:
            file.write("version=\n")
            file.write("autosave=")
        print("Created:", server_functions.bot_properties_file)
    except: print("Error: Setting up Discord-bot.properties file at:", server_functions.server_path)


def start_tmux_session():
    try:
        os.system('tmux new -d -s mcserver')
        print("Started Tmux 'mcserver' detached session.")
    except: print("Error: Starting 'mcserver' detached session.")

    try:
        os.system('tmux send-keys -t mcserver:1.0 "tmux split-window -v" ENTER')
        print("Created second tmux pane for Discord bot.")
    except: print("Error: Creating second tmux pane for Discord bot.")
    time.sleep(1)

def start_bot():
    os.system(f'tmux send-keys -t mcserver:1.1 "cd {server_functions.server_functions_path}" ENTER')
    if not os.system("tmux send-keys -t mcserver:1.1 'python3 discord_mc_bot.py' ENTER"): return True  # If os.system() return 0, means successful.

def script_help():
    help = """
    python3 run_bot.py setup download run tmuxattach  --  Creates required folders, downloads latest server.jar, starts MC server and bot in Tmux, and attach to tmux session.
    python3 run_bot.py tmuxstart run tmuxattach  --  Starts Tmux session, starts MC server and bot, then attaches to Tmux.
    
    server_files_access, use_rcon, and use_tmux boolean variables are in server_functions.py. update these for your setup.
    
    setup       --  If server_files_access is True, sets up necessary folders. Then, if use_tmux is True, starts Tmux session named 'mcserver' in detached mode with 2 panes.
                    Folders created: server, server_backups, and world_backs. If use_tmux is also True this will also start tmux session.
                        
    update    --  If server_files_access is True, Downloads latest server.jar file from official Minecraft website to /server folder.
    
    tmuxstart   --  If use_tmux is True, starts a Tmux session named 'mcserver' with 2 panes. 
                    Top pane for Minecraft server, and bottom pane is for Discord bot.
                    
    tmuxsattach --  If use_tmux is True, attaches to 'mcserver' session. 
                    This will not start session if it doesn't exist, use 'setup' or 'tmux' argument to setup session.
                    
    run         --  This is the same as running run_bot.py without any arguments. 
                    This will start Minecraft server (if use_tmux) and start Discord bot either in Tmux session or in current console depending on use_tmux boolean.
    
    help        --  Shows this help page.
    
    Note:   The corresponding functions will run in the order you pass arguments in. 
            For example, 'python3 run_bot.py run tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
            Instead run 'python3 tmuxstart run tmuxattach', which will start a Tmux session then start server and bot, then attach to Tmux session.
    """
    print(help)


if __name__ == '__main__':
    # Initial directory and Tmux setup.
    if 'setup' in sys.argv:
        if server_functions.server_files_access:
            setup_directories()
        if server_functions.use_tmux:
            start_tmux_session()
        if server_functions.use_rcon:
            print("Using RCON. Make sure relevant variables are set properly in server_functions.py.")

    # Start 'mcserver' tmux detached session.
    if 'tmuxstart' in sys.argv and server_functions.use_tmux: start_tmux_session()

    # Download latest server.jar.
    if 'update' in sys.argv and server_functions.server_files_access:
        print("Downloading latest server.jar from Minecraft website...")
        server_functions.download_new_server()
        print("Downloaded server.jar to:", server_functions.server_path)

    # Start Minecraft server and/or Discord bot.
    if len(sys.argv) == 1 or 'run' in sys.argv:
        if server_functions.use_subprocess:
            print("Start server with ?start command in Discord")
            input("Enter to continue > ")
        if server_functions.use_tmux:
            start_bot()
            server_functions.mc_start()
            print("Started bot in 'mcserver' tmux session top pane.")
        else: bot.run(TOKEN)

    # Attach to 'mcserver' tmux session.
    if 'tmuxattach' in sys.argv: os.system("tmux attach -t mcserver")

    if 'help' in sys.argv: script_help()
