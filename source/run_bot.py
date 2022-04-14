import subprocess, psutil, time, sys, os
from slime_bot import bot, TOKEN
from slime_vars import tmux_session_name, pyenv_activate_command
from backend_functions import lprint
import backend_functions, slime_vars

ctx = 'run_bot.py'  # So you know which log lines come from which file.
slime_proc = slime_pid = None  # If using nohup to run bot in background.
slime_proc_name, slime_proc_cmdline = 'python3',  'slime_bot.py'  # Needed to find correct process if multiple python process exists.
watch_interval = 1  # How often to update log file. watch -n X tail bot_log.txt

def setup_directories():
    """Create necessary directories."""
    try:
        # TODO Needed?
        # Creates Server folder, folder for world backups, and folder for server backups.
        os.makedirs(slime_vars.server_path)
        lprint(ctx, "INFO: Created: " + slime_vars.server_path)
        os.makedirs(slime_vars.world_backups_path)
        lprint(ctx, "INFO: Created: " + slime_vars.world_backups_path)
        os.makedirs(slime_vars.server_backups_path)
        lprint(ctx, "INFO: Created: " + slime_vars.server_backups_path)
    except:
        lprint(ctx, "ERROR: Creating folder structure at: " + slime_vars.server_path)

def start_tmux_session():
    """Starts Tmux session in detached mode, with 2 panes, and sets name."""
    if os.system(f'tmux new -d -s {tmux_session_name}'):
        lprint(ctx, f"ERROR: Starting tmux session")
    else: lprint(ctx, f"INFO: Started Tmux detached session")

    if os.system(f'tmux split-window -v -t {tmux_session_name}:0.0'):
        lprint(ctx, "ERROR: Creating second tmux panes")
    else: lprint(ctx, "INFO: Created second tmux panes")

    time.sleep(1)

def start_bot():
    if slime_vars.use_tmux is True:
        # Sources pyenv if set in slime_vars.
        if os.system(f'tmux send-keys -t {tmux_session_name}:0.1 "cd {slime_vars.bot_files_path}" ENTER'):
            lprint(ctx, "ERROR: Changing directory to bot path. (Bot may continue to work anyways)")

        if os.system(f"tmux send-keys -t {tmux_session_name}:0.1 'python3 slime_bot.py' ENTER"):
            lprint(ctx, "ERROR: Starting slime_bot.py")
        else: lprint(ctx, "INFO: Started slime_bot.py")

def server_start():
    """Start Minecraft server, method varies depending on variables set in slime_vars.py."""
    if slime_vars.use_tmux is True:
        backend_functions.server_start()
    else: bot.run(TOKEN)

# ===== Background process (nohup)
def start_slime_proc():
    """Starts bot in background with subprocess.Popen()."""
    global slime_proc, slime_pid

    if pyenv_activate_command:
        if os.system(f"tmux send-keys -t {tmux_session_name}:0.1 '{pyenv_activate_command}' ENTER"):  # Sources pyenv if set in slime_vars.:
            lprint(ctx, "ERROR: Activating pyenv")
        else: lprint(ctx, "INFO: Activated pyenv")

    if os.system(f'tmux send-keys -t {tmux_session_name}:0.1 "cd {slime_vars.bot_files_path}" ENTER'):
        lprint(ctx, "ERROR: Changing directory to bot path. (Bot may continue to work anyways)")
    subprocess.Popen(['python3', f'{slime_vars.bot_files_path}/slime_bot.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Sets slime_proc and slime_pid variable so bot can be stopped with a Discord command.
    if proc := backend_functions.get_proc(slime_proc_name, slime_proc_cmdline):
        slime_proc = proc
        slime_pid = proc.pid
        backend_functions.set_slime_proc(slime_proc, slime_pid)
        lprint(ctx, f"INFO: Process PID Found: {proc.pid}")
    else: lprint(ctx, "ERROR: Finding  process PID")

def kill_slime_proc():
    """Kills bot process."""
    if proc := backend_functions.get_proc(slime_proc_name, slime_proc_cmdline):
        proc.kill()
        lprint(ctx, "INFO: Bot process killed")
    else: lprint(ctx, "ERROR: Bot process not found")

def status_slime_proc():
    """Get bot process name and pid."""
    if proc := backend_functions.get_proc(slime_proc_name, slime_proc_cmdline):
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
    showlog     - Show bot log using 'watch -n X tail .../bot_log.txt' command. To get out of it, use ctrl + c.
                  Use standalone, showlog will not work properly if used with other arguments.
    attachtmux  - Attaches to session. Will not start Tmux, use starttmux or setup.
    --popen     - Run with subprocess.Popen(). Currently needed to use valheim comannds.
        E.g. python3 run_bot.py --popen startbot

    NOTE:   The corresponding functions will run in the order you pass arguments in.
            For example, 'python3 run_bot.py startbot tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
            Instead run 'python3 tmuxstart startboth tmuxattach', start Tmux session then start server and bot, then attach to Tmux session.
    
    WARN:   If using nohup method, having a similar process (including it's command arguments) name to slime_bot.py will cause issues.
            Say if you have a vim open editing slime_var.py, this script will may mistake that for the bot. 
            From my testing this is unpredictable, sometimes it'll work and sometimes not. Until I can find a fix, just be careful.
    """
    print(help)


if __name__ == '__main__':
    # The order of the if statements is important.

    if 'setup' in sys.argv:
        if slime_vars.server_files_access is True:
            setup_directories()
        if slime_vars.use_tmux is True:
            start_tmux_session()
        if slime_vars.use_rcon is True:
            print("Using RCON. Make sure relevant variables are set properly in backend_functions.py.")

    if 'starttmux' in sys.argv and slime_vars.use_tmux:
        start_tmux_session()
        time.sleep(1)

    if 'startbot' in sys.argv:
        if '--popen' in sys.argv:
            start_slime_proc()
        else: start_bot()

    # Background process method (using nohup)
    if 'stopbot' in sys.argv:
        kill_slime_proc()
    if 'statusbot' in sys.argv: status_slime_proc()

    if 'startserver' in sys.argv: server_start()

    if 'startboth' in sys.argv:
        server_start()
        start_bot()

    if 'showlog' in sys.argv: show_log()

    # My personal shortcut.
    if 'slime' in sys.argv:
        start_tmux_session()
        time.sleep(1)
        start_bot()
        os.system(f"tmux attach -t {tmux_session_name}")

    if 'attachtmux' in sys.argv: os.system(f"tmux attach -t {tmux_session_name}")

    if 'help' in sys.argv: script_help()
