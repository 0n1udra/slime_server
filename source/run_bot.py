#!/usr/bin/python3

import json, time, sys, os
import bot_files.slime_vars as slime_vars
from bot_files.slime_bot import bot
from bot_files.extra import lprint, update_from_user_config
import bot_files.backend_functions as backend

ctx = 'run_bot.py'  # So you know which log lines come from which file.
watch_interval = 1  # How often to update log file. watch -n X tail bot_log.txt
beta_mode = ''

def setup_config():
    global slime_vars
    # Creates flatten dict to make it easier to find items to use as defaults
    default_configs = {**slime_vars.config['bot_config'].copy(), **slime_vars.config['servers']['example'].copy()}
    def get_input(config_prompts):
        config = {}
        for variable, prompt in config_prompts.items():
            default_value = default_configs.get(variable, "''")
            input_type = type(default_value)
            config_input = input(f"{prompt} [{default_value}]: ").strip() or default_value  # Uses default value if enter nothing.
            if input_type is bool:
                if str(config_input).lower() in ['y', 'yes']:
                    config[variable] = True
                if str(config_input).lower() in ['n', 'no']:
                    config[variable] = False
            else:
                try: config[variable] = input_type(config_input) if input_type else config_input  # Converts to needed type.
                except:
                    config[variable] = default_value
                    print("Using default:", default_value)
        return config

    bot_config_prompts = {
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
    bot_configs = get_input(bot_config_prompts)

    # Asks to continue to server configs
    server_configs = {}
    ask_input = input(f"\nContinue to server config (y/n): ").strip().lower()
    if ask_input in ['y', 'yes']: server_configs = get_input(server_config_prompts)

    # Updates dictionaries and returns new dictionary to update slime_vars.config
    updated_bot_configs = slime_vars.config['bot_config']
    updated_bot_configs.update(bot_configs)
    example_server_configs = slime_vars.config['servers']['example'].copy()
    updated_server_configs = example_server_configs.copy()
    updated_server_configs.update(server_configs)

    slime_vars.update_vars({'bot_config': updated_bot_configs, 'servers': {updated_server_configs['server_name']: updated_server_configs,
                                                                           'example': example_server_configs}})
    try: open(user_config_filepath, 'a').close()
    except: lprint(ctx, "ERROR: Unable to create 'user_config.json' file.")
    else:  # Creates new json
        with open(user_config_filepath, "w") as outfile: outfile.write(json.dumps(slime_vars.config, indent=4))
        lprint(ctx, "INFO: New user_config.json created.")


def _start_bot():
    """Starts Discord bot. This is a separate function incase you want to run the bot inline."""
    if os.path.isfile(slime_vars.bot_token_filepath):
        with open(slime_vars.bot_token_filepath, 'r') as file:
            TOKEN = file.readline()
            lprint(ctx, f'INFO: Discord Token: {slime_vars.bot_token_filepath}')
    else:
        lprint(ctx, f"ERROR: Missing Token File: {slime_vars.bot_token_filepath}")
        sys.exit()

    bot.run(TOKEN)

def start_bot():
    """Uses different methods of launching Discord bot depending on config"""
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
        if slime_vars.use_pyenv:
            if os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane} "{slime_vars.pyenv_activate_command}" ENTER'):
                lprint(ctx, f"ERROR: {slime_vars.pyenv_activate_command}")
            else: lprint(ctx, f"INFO: Activated pyenv")

        if os.system(f"tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_bot_pane} '{slime_vars.bot_launch_command} {beta_mode}' ENTER"):
            lprint(ctx, "ERROR: Could not start bot in tmux. Will run bot here.")
            _start_bot()
        else: lprint(ctx, "INFO: Started slime_bot.py")

    else: _start_bot()  # Starts inline if not using tmux.

def setup_directories():
    """Create necessary directories."""

    # Creates Server folder, folder for world backups, and folder for server backups.
    os.makedirs(slime_vars.servers_path)
    lprint(ctx, "INFO: Created: " + slime_vars.servers_path)
    os.makedirs(slime_vars.server_path)
    lprint(ctx, "INFO: Created: " + slime_vars.server_path)
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

def show_log():
    """Use watch + tail command on bot log."""

    os.system(f"watch -n {watch_interval} tail {slime_vars.bot_log_filepath}")

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

def show_banner():
    # Hides sensitive info from output.
    nono = slime_vars.show_sensitive_info  # what? got a problem with the naming? it works.
    no = '**********'  # 2bad. change it!

    vars_msg = f"""
Bot:
Version             {slime_vars.__version__} - {slime_vars.__date__}
User                {slime_vars.user}
Python Env          {slime_vars.pyenv_activate_command if slime_vars.use_pyenv else 'None'}
Subprocess          {slime_vars.server_use_subprocess}
Tmux                {slime_vars.use_tmux}
RCON                {slime_vars.server_use_rcon}
Bot Log             {slime_vars.bot_log_filepath}

Discord:
Discord Token       {slime_vars.bot_token_filepath if nono else no}
Command Prefix      {slime_vars.command_prefix}
Case Insensitive    {slime_vars.case_insensitive}
Intents             {slime_vars.intents}
Channel ID          {slime_vars.channel_id if nono else no}
Show Custom Status  {slime_vars.enable_status_checker} - {slime_vars.custom_status_interval}min

Server:
Minecraft Folder    {slime_vars.mc_path}
File Access         {slime_vars.server_files_access}
Autosave            {slime_vars.enable_autosave} - {slime_vars.autosave_interval}min
Server URL          {slime_vars.server_address if nono else no}
Server Port         {slime_vars.server_port if nono else no}
"""
    if slime_vars.use_tmux: vars_msg += f"""
Tmux:
Session Name        {slime_vars.tmux_session_name}
Bot Pane            {slime_vars.tmux_bot_pane}
Server Pane         {slime_vars.tmux_minecraft_pane}
"""

    if slime_vars.server_use_screen: vars_msg += f"""
Screen:
Session Name        {slime_vars.screen_session_name}
"""

    if slime_vars.server_use_rcon: vars_msg += f"""
RCON:
Pass                {slime_vars.rcon_pass if nono else no}
Port                {slime_vars.rcon_port if nono else no}
"""

    if slime_vars.server_files_access: vars_msg += f"""
Local Server:
Minecraft Path      {slime_vars.mc_path}
Server Path         {slime_vars.server_path}
"""

    print(vars_msg)

if __name__ == '__main__':
    user_config_filepath = slime_vars.user_config_filepath
    if os.path.isfile(user_config_filepath):  # Creates user_config.json if not exist.
        loaded_configs = update_from_user_config(slime_vars.config)
        slime_vars.update_vars(loaded_configs)
        lprint(ctx, "INFO: Loaded user_config.json.")
    else:
        lprint(ctx, "INFO: No 'user_config.json' file detected.")
        setup_config()

    # The order of the if statements is important.
    if 'hidebanner' not in sys.argv: show_banner()

    if not slime_vars.channel_id:
        lprint(ctx, "INFO: To enable startup message banner in discord, use '?setchannel' in the channel you want it in.")

    if 'setup' in sys.argv:
        if slime_vars.server_files_access is True:
            setup_directories()
        if slime_vars.server_use_rcon is True:
            lprint(ctx, "INFO: RCON Enabled. Make sure relevant variables are set properly in backend.py.")

    if 'beta' in sys.argv:
        beta_mode = 'beta'
        slime_vars.bot_token_filepath = os.path.join(slime_vars.home_dir, 'keys', 'slime_bot_beta.token')
        slime_vars.channel_id = '916450451061350420'

    if 'starttmux' in sys.argv and slime_vars.use_tmux:
        start_tmux_session()
        time.sleep(1)

    if 'startbot' in sys.argv:
        start_bot()

    if '_startbot' in sys.argv:
        _start_bot()

    # Background process method (using nohup)
    if 'stopbot' in sys.argv:
        backend.kill_slime_proc()

    if 'statusbot' in sys.argv: backend.status_slime_proc()

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

