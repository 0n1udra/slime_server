import os, sys, time, server_functions
from discord_mc_bot import bot, TOKEN

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


def script_help():
    help = """
    python3 run_bot.py setup download attach  --  Creates required folders, downloads latest server.jar, and attach to tmux session.
    
    server_files_access, use_rcon, and use_tmux boolean variables are in server_functions.py. update these for your setup.
    
    setup       --  If server_files_access is True, sets up necessary folders. 
                    Folders created: server, server_backups, and world_backs. If use_tmux is also True this will also start tmux session.
                        
    download    --  If server_files_access is True, Downloads latest server.jar file from official Minecraft website to /server folder.
    
    tmux        --  If use_tmux is True, starts a Tmux session named 'mcserver' with 2 panes. 
                    Top pane for Minecraft server, and bottom pane is for Discord bot.
                    
    attach      --  If use_tmux is True, attaches to 'mcserver' session. 
                    This will not start session if it doesn't exist, use 'setup' or 'tmux' argument to setup session.
                    
    run         --  This is the same as running run_bot.py without any arguments. 
                    This will start Minecraft server (if use_tmux) and start Discord bot either in Tmux session or in current console depending on use_tmux boolean.
    
    help        --  Shows this help page.
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
    if 'tmux' in sys.argv and server_functions.use_tmux: start_tmux_session()

    # Download latest server.jar.
    if 'download' in sys.argv and server_functions.server_files_access:
        print("Downloading latest server.jar from Minecraft website...")
        server_functions.download_new_server()
        print("Downloaded server.jar to:", server_functions.server_path)

    # Start Minecraft server and/or Discord bot.
    if len(sys.argv) == 1 or 'run' in sys.argv:
        if server_functions.use_tmux:
            server_functions.start_minecraft_server()
            print("Started Minecraft server in 'mcserver' tmux session pane 0.")
            server_functions.start_discord_bot()
            print("Started Discord bot in 'mcserver' tmux session pane 1.")
        else: bot.run(TOKEN)

    # Attach to 'mcserver' tmux session.
    if 'attach' in sys.argv: os.system("tmux attach -t mcserver")

    if 'help' in sys.argv: script_help()
