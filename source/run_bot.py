#!/usr/bin/python3

import os
import sys
import time

from bot_files.slime_config import config, __version__, __date__
from bot_files.slime_bot import bot
from bot_files.slime_utils import lprint, file_utils, proc_utils

watch_interval = 1  # How often to update log file. watch -n X tail bot_log.txt
beta_mode = ''

def setup_configs():
    # Creates flatten dict to make it easier to find items to use as defaults
    def get_input(config_prompts):
        new_configs = {}
        for variable, prompt in config_prompts.items():
            default_value = config.get_config(variable)
            input_type = type(default_value)
            config_input = input(f"{prompt} [{default_value}]: ").strip() or default_value  # Uses default value if enter nothing.
            if input_type is bool:
                if str(config_input).lower() in ['y', 'yes']:
                    new_configs[variable] = True
                if str(config_input).lower() in ['n', 'no']:
                    new_configs[variable] = False
            else:
                try:
                    new_configs[variable] = input_type(config_input) if input_type else config_input  # Converts to needed type.
                except:
                    new_configs[variable] = default_value
                    print("Using default:", default_value)
        return new_configs

    bot_config_prompts = {
        'pyenv_activate_command': 'Command to use to activate/source pyenv if using one.',
        "use_pyenv": "Use Python env (y/n)",
        'bot_token_filepath': "Discord bot token filepath",
        'command_prefix': "Discord command prefix",
        'channel_id': "Channel ID to send startup message in.",
        'mc_path': "Path for MC servers and their backups",
        'tmux_session_name': "Tmux session name",
        'use_tmux': "Use Tmux (y/n)"
    }
    server_config_prompts = {  # Optionally setup server
        'server_name': "Server name",
        'server_description': "Server description",
        'server_address': "Server domain/IP",
        'server_port': "Server port",
        'server_files_access': "Bot can access MC files locally (y/n)",
        'rcon_pass': 'RCON password',
        'rcon_port': 'RCON Port',
        'server_use_rcon': 'Enable RCON',
    }

    print("----- Config Setup -----\nPress enter to use default.")
    config.bot_configs.update(get_input(bot_config_prompts))

    # Asks to continue to server configs
    ask_input = input(f"\nContinue to server config (y/n): ").strip().lower()
    if ask_input in ['y', 'yes']:
        config.example_server_configs.update(get_input(server_config_prompts))

    config.update_all_server_configs()  # Updates paths configs, and writes to file.

def _start_bot():
    """Starts Discord bot. This is a separate function incase you want to run the bot inline."""
    if os.path.isfile(config.get_config('bot_token_filepath')):
        with open(config.get_config('bot_token_filepath'), 'r') as file:
            TOKEN = file.readline()
            lprint(f"INFO: Discord Token: {config.get_config('bot_token_filepath')}")
    else:
        lprint(f"ERROR: Missing Token File: {config.get_config('bot_token_filepath')}")
        sys.exit()

    bot.run(TOKEN)

def start_bot():
    """Uses different methods of launching Discord bot depending on config"""
    if config.get_config('use_tmux'):
        no_tmux = False
        # Sources pyenv if set in slime_vars.
        x = f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_bot_pane')} 'cd {config.get_config('bot_source_path')}' ENTER"
        if os.system(x):
            lprint(f"ERROR: Changing directory ({config.get_config('bot_source_path')})")
            no_tmux = True

        if no_tmux:
            _start_bot()
            return

        # Activate python env.
        if config.get_config('use_pyenv'):
            if os.system(f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_bot_pane')} '{config.get_config('pyenv_activate_command')}' ENTER"):
                lprint(f"ERROR: {config.get_config('pyenv_activate_command')}")
            else: lprint(f"INFO: Activated pyenv")

        if os.system(f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_bot_pane')} '{config.get_config('bot_launch_command')} {beta_mode}' ENTER"):
            lprint("ERROR: Could not start bot in tmux. Will run bot here.")
            _start_bot()
        else: lprint("INFO: Started slime_bot.py")

    else: _start_bot()  # Starts inline if not using tmux.

def start_tmux_session():
    """Starts Tmux session in detached mode, with 2 panes, and sets name."""

    if os.system(f"tmux new -d -s {config.get_config('tmux_session_name')}"):
        lprint(f"ERROR: Starting tmux session")
    else: lprint(f"INFO: Started Tmux detached session")

    if os.system(f"tmux split-window -v -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_bot_pane')}"):
        lprint("ERROR: Creating second tmux panes")
    else: lprint("INFO: Created second tmux panes")

    time.sleep(1)

def show_log():
    """Use watch + tail command on bot log."""

    os.system(f"watch -n {watch_interval} tail {config.get_config('bot_log_filepath')}")

def script_help():
    help = """
    python3 run_bot.py setup download startboth            --  Create required folders, downloads latest server.jar, and start server and bot with Tmux.
    python3 run_bot.py tmuxstart startboth tmuxattach      --  Start Tmux session, start server and bot, then attaches to Tmux session.
    
    help        - Shows this help page.
    setup       - Create necessary folders. Starts Tmux session in detached mode with 2 panes.
    starttmux   - Start Tmux session named with 2 panes. Top pane for Minecraft server, bottom for bot.
    startbot    - Start Discord bot.
    stopbot     - Stops Discord bot.
    attachtmux  - Attaches to session. Will not start Tmux, use starttmux or setup.
    log         - Show bot log using 'watch -n X tail .../bot_log.txt' command. To get out of it, use ctrl + c.
                  Use standalone, showlog will not work properly if used with other arguments.

    NOTE:   The corresponding functions will run in the order you pass arguments in.
            For example, 'python3 run_bot.py startbot tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
            Instead run 'python3 tmuxstart startboth tmuxattach', start Tmux session then start server and bot, then attach to Tmux session.
    """
    print(help)

def show_banner():
    # Hides sensitive info from output.
    nono = config.get_config('show_sensitive_info')  # what? got a problem with the naming? it works.
    no = '**********'  # 2bad. change it!

    vars_msg = f"""
NOTE: More config info in README.md or read comments in slime_config.py file in bot_files.
Bot:
Version             {__version__} - {__date__}
User                {config.get_config('user')}
Python Env          {config.get_config('pyenv_activate_command') if config.get_config('use_pyenv') else 'None'}
Subprocess          {config.get_config('server_use_subprocess')}
Tmux                {config.get_config('use_tmux')}
RCON                {config.get_config('server_use_rcon')}
Bot Log             {config.get_config('bot_log_filepath')}

Discord:
Discord Token       {config.get_config('bot_token_filepath') if nono else no}
Command Prefix      {config.get_config('command_prefix')}
Case Insensitive    {config.get_config('case_insensitive')}
Intents             {config.intents}
Channel ID          {config.get_config('channel_id') if nono else no}
Show Custom Status  {config.get_config('check_before_command')} - {config.get_config('custom_status_interval')}min

Server:
Minecraft Folder    {config.get_config('mc_path')}
File Access         {config.get_config('server_files_access')}
Autosave            {config.get_config('enable_autosave')} - {config.get_config('autosave_interval')}min
Server URL          {config.get_config('server_address') if nono else no}
Server Port         {config.get_config('server_port') if nono else no}
"""
    if config.get_config('use_tmux'): vars_msg += f"""
Tmux:
Session Name        {config.get_config('tmux_session_name')}
Bot Pane            {config.get_config('tmux_bot_pane')}
Server Pane         {config.get_config('tmux_minecraft_pane')}
"""

    if config.get_config('server_use_screen'): vars_msg += f"""
Screen:
Session Name        {config.get_config('screen_session_name')}
"""

    if config.get_config('server_use_rcon'): vars_msg += f"""
RCON:
Pass                {config.get_config('rcon_pass') if nono else no}
Port                {config.get_config('rcon_port') if nono else no}
"""

    if config.get_config('server_files_access'): vars_msg += f"""
Local Server:
Minecraft Path      {config.get_config('mc_path')}
Server Path         {config.get_config('server_path')}
"""

    print(vars_msg)


if __name__ == '__main__':
    if config.get_config('init') is False:
        lprint("INFO: Initializing config.")
        setup_configs()  # This will call config.update_all_server_configs which will creates user_config.json if not exist.
        config.set_config('init', True)
    else:
        config.update_from_file()
        lprint("INFO: Loaded user_config.json.")

    # The order of the if statements is important.
    if 'hidebanner' not in sys.argv: show_banner()

    if not config.get_config('channel_id'):
        lprint("INFO: To enable startup message banner in discord, use '?setchannel' in the channel you want it in.")

    if 'setup' in sys.argv:
        if config.get_config('server_files_access'):
            file_utils.setup_directories()
        if config.get_config('server_use_rcon'):
            lprint("INFO: RCON Enabled. Make sure relevant variables are set properly in backend.py.")

    if 'beta' in sys.argv:
        beta_mode = 'beta'
        config.set_config('bot_token_filepath', os.path.join(config.get_config('home_path'), 'keys', 'slime_bot_beta.token'))

    if 'starttmux' in sys.argv and config.get_config('use_tmux'):
        start_tmux_session()
        time.sleep(1)

    if 'startbot' in sys.argv:
        start_bot()

    if '_startbot' in sys.argv:
        _start_bot()

    # Background process method (using nohup)
    if 'stopbot' in sys.argv:
        proc_utils.kill_slime_proc()

    if 'statusbot' in sys.argv: proc_utils.status_slime_proc()

    if 'log' in sys.argv: show_log()

    # My personal shortcut.
    if 'slime' in sys.argv:
        start_tmux_session()
        time.sleep(1)
        start_bot()
        os.system(f"tmux attach -t {config.get_config('tmux_session_name')}")

    if 'attachtmux' in sys.argv: os.system(f"tmux attach -t {config.get_config('tmux_session_name')}")

    if 'help' in sys.argv: script_help()

