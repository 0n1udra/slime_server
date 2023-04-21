#!/usr/bin/python3

import time, sys, os
from bot_files.slime_bot import bot
from bot_files.extra import lprint
import bot_files.backend_functions as backend
import slime_vars

ctx = 'run_bot.py'  # So you know which log lines come from which file.
slime_proc = slime_pid = None  # If using nohup to run bot in background.
slime_proc_name, slime_proc_cmdline = 'python3',  'slime_bot.py'  # Needed to find correct process if multiple python process exists.
watch_interval = 1  # How often to update log file. watch -n X tail bot_log.txt
beta_mode = ''

def _start_bot():
    if os.path.isfile(slime_vars.bot_token_file):
        with open(slime_vars.bot_token_file, 'r') as file:
            TOKEN = file.readline()
            lprint(ctx, f'INFO: Using token: {slime_vars.bot_token_file}')
    else:
        lprint(ctx, f"ERROR: Missing Token File: {slime_vars.bot_token_file}")
        sys.exit()

    bot.run(TOKEN)

def start_bot():
    if slime_vars.use_tmux is True:
        no_tmux = False
        # Sources pyenv if set in slime_vars.
        if os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane} "cd {slime_vars.bot_src_path}" ENTER'):
            lprint(ctx, f"ERROR: Changing directory ({slime_vars.bot_src_path})")
            no_tmux = True

        if no_tmux:
            _start_bot()
            return

        # Activate python env.
        if slime_vars.pyenv_activate_command:
            if os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane} "{slime_vars.pyenv_activate_command}" ENTER'):
                lprint(ctx, f"ERROR: {slime_vars.pyenv_activate_command}")
            else: lprint(ctx, f"INFO: Activated pyenv")

        if os.system(f"tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane} 'python3 run_bot.py _startbot {beta_mode}' ENTER"):
            lprint(ctx, "ERROR: Could not start bot in tmux. Will run bot here.")
            _start_bot()
        else: lprint(ctx, "INFO: Started slime_bot.py")

    else: _start_bot()

def setup_directories():
    """Create necessary directories."""

    # Creates Server folder, folder for world backups, and folder for server backups.
    os.makedirs(slime_vars.servers_path)
    lprint(ctx, "INFO: Created: " + slime_vars.servers_path)
    os.makedirs(slime_vars.world_backups_path)
    lprint(ctx, "INFO: Created: " + slime_vars.world_backups_path)
    os.makedirs(slime_vars.server_backups_path)
    lprint(ctx, "INFO: Created: " + slime_vars.server_backups_path)

def start_tmux_session():
    """Starts Tmux session in detached mode, with 2 panes, and sets name."""

    if os.system(f'tmux new -d -s {slime_vars.tmux_session_name}'):
        lprint(ctx, f"ERROR: Starting tmux session")
    else: lprint(ctx, f"INFO: Started Tmux detached session")

    if os.system(f'tmux split-window -v -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane}'):
        lprint(ctx, "ERROR: Creating second tmux panes")
    else: lprint(ctx, "INFO: Created second tmux panes")

    time.sleep(1)

def server_start():
    """Start Minecraft server, method varies depending on variables set in slime_vars.py."""

    if slime_vars.use_tmux is True:
        backend.server_start()

def kill_slime_proc():
    """Kills bot process."""

    if proc := backend.get_proc(slime_proc_name, slime_proc_cmdline):
        proc.kill()
        lprint(ctx, "INFO: Bot process killed")
    else: lprint(ctx, "ERROR: Bot process not found")

def status_slime_proc():
    """Get bot process name and pid."""

    if proc := backend.get_proc(slime_proc_name, slime_proc_cmdline):
        lprint(ctx, f"INFO: Process info: {proc.name()}, {proc.pid}")

def show_log():
    """Use watch + tail command on bot log."""

    os.system(f"watch -n {watch_interval} tail {slime_vars.bot_log_file}")

def script_help():
    help = """
    python3 run_bot.py setup download startboth            --  Create required folders, downloads latest server.jar, and start server and bot with Tmux.
    python3 run_bot.py tmuxstart startboth tmuxattach      --  Start Tmux session, start server and bot, then attaches to Tmux session.
    
    help        - Shows this help page.
    setup       - Create necessary folders. Starts Tmux session in detached mode with 2 panes.
    starttmux   - Start Tmux session named with 2 panes. Top pane for Minecraft server, bottom for bot.
    startbot    - Start Discord bot.
    stopbot     - Stops Discord bot.
    startserver - Start MC server.
    startboth   - Start Minecraft server and bot either using Tmux or in current console depending on corresponding variables.
    attachtmux  - Attaches to session. Will not start Tmux, use starttmux or setup.
    log         - Show bot log using 'watch -n X tail .../bot_log.txt' command. To get out of it, use ctrl + c.
                  Use standalone, showlog will not work properly if used with other arguments.

    NOTE:   The corresponding functions will run in the order you pass arguments in.
            For example, 'python3 run_bot.py startbot tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
            Instead run 'python3 tmuxstart startboth tmuxattach', start Tmux session then start server and bot, then attach to Tmux session.
    """
    print(help)

vars_msg = f"""
Bot:
    User                {slime_vars.user}
    Python Env          {slime_vars.pyenv_activate_command}
    Subprocess          {slime_vars.use_subprocess}
    Tmux                {slime_vars.use_tmux}
    RCON                {slime_vars.use_rcon}
    Bot Log             {slime_vars.bot_log_file}
    
Discord:
    Discord Token       {slime_vars.bot_token_file}
    Command Prefix      {slime_vars.command_prefex}
    Case Insensitive    {slime_vars.case_insensitive}
    Intents             {slime_vars.intents}
    Channel ID          {slime_vars.channel_id}

Server:
    Autosave            {slime_vars.autosave_status} - {slime_vars.autosave_interval}
    File Access         {slime_vars.server_files_access}
    Server Selected     {slime_vars.server_selected}
    Server URL          {slime_vars.server_url}
    Server Port         {slime_vars.server_port}
"""
if slime_vars.use_tmux:
    vars_msg += f"""
Tmux:
    Session Name        {slime_vars.tmux_session_name}
    Bot Pane            {slime_vars.tmux_bot_pane}
    Server Pane         {slime_vars.tmux_minecraft_pane}
"""

if slime_vars.use_rcon:
    vars_msg += f"""
RCON:
    Pass                {slime_vars.rcon_pass}
    Port                {slime_vars.rcon_port}
    """

if slime_vars.server_files_access:
    vars_msg += f"""
Local Server:
    Minecraft Path      {slime_vars.mc_path}
    Server Path         {slime_vars.server_path}
    """

if __name__ == '__main__':
    # The order of the if statements is important.
    print(vars_msg)

    if 'setup' in sys.argv:
        if slime_vars.server_files_access is True:
            setup_directories()
        if slime_vars.use_rcon is True:
            lprint(ctx, "INFO: Using RCON. Make sure relevant variables are set properly in backend.py.")

    if 'beta' in sys.argv:
        beta_mode = 'beta'
        slime_vars.bot_token_file = f'C:\\Users\\0n1udra\\keys\\slime_bot_beta.token'
        #slime_vars.bot_token_file = f'/home/{slime_vars.user}/keys/slime_bot_beta.token'
        slime_vars.channel_id = 916450451061350420

    if 'starttmux' in sys.argv and slime_vars.use_tmux:
        start_tmux_session()
        time.sleep(1)

    if 'startbot' in sys.argv:
        start_bot()

    if '_startbot' in sys.argv:
        _start_bot()

    # Background process method (using nohup)
    if 'stopbot' in sys.argv:
        kill_slime_proc()

    if 'statusbot' in sys.argv: status_slime_proc()

    if 'startserver' in sys.argv: server_start()

    if 'startboth' in sys.argv:
        server_start()
        start_bot()

    if 'log' in sys.argv: show_log()

    # My personal shortcut.
    if 'slime' in sys.argv:
        start_tmux_session()
        time.sleep(1)
        start_bot()
        os.system(f"tmux attach -t {slime_vars.tmux_session_name}")

    if 'attachtmux' in sys.argv: os.system(f"tmux attach -t {slime_vars.tmux_session_name}")

    if 'help' in sys.argv: script_help()

