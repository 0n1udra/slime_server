#!/usr/bin/python3

__version__ = '9.0.3'
__date__ = '02/11/2023'
__license__ = 'GPL 3'
__author__ = 'github.com/0n1udra'
__discord__ = 'https://discord.gg/s58XgzhE3U'  # Join for bot help (if i'm online :)

import os
import sys
import platform
import subprocess

from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils, file_utils, proc_utils

watch_interval = 1  # How often to update log file. watch -n X tail bot_log.txt

class Slime_Bot:
    def __init__(self):
        self.dev_mode = ''
        if 'dev' in sys.argv:
            self.dev_mode = 'dev'

        # Use Windows config file.
        if platform.system() == 'Windows' and self.dev_mode:
            config._win_mode = True

        # Asks for some basic configs if no config file found.
        if not config.update_from_file() or config.get_config('init') is False:
            lprint("INFO: Initializing config.")
            self.config_prompts()  # This will call config.update_all_configs which will creates user_config.json if not exist.
        else: lprint("INFO: Loaded user_config.json.")

        # Start bot in a tmux or screen session or else in line.
        self.bot_session = ''
        if config.get_config('bot_use_tmux'):
            self.bot_session = 'tmux'
        elif config.get_config('bot_use_screen'):
            self.bot_session = 'screen'

        self.tmux_name = config.get_config('bot_tmux_name')
        self.tmux = f"{self.tmux_name}:{config.get_config('bot_tmux_pane')}"
        self.screen_name = config.get_config('bot_screen_name')
        self.parse_runtime_args()

    def parse_runtime_args(self):
        # The order of the if statements is important.

        # Hides banner
        if 'hidebanner' not in sys.argv:
            if config.get_config('use_pyenv'):
                if sys.prefix == sys.base_prefix:
                    self.show_banner()
            else: self.show_banner()

        # Use custom token and configs.
        if self.dev_mode:
            config.set_config('bot_token_filepath', f"{config.get_config('home_path')}//keys//slime_bot_beta.token", save=False)
            lprint("INFO: Using dev mode.")

        # Setup needed folders: servers, server_backups, world_backups
        if 'makefolders' in sys.argv:
            file_utils.setup_directories()
            return

        if 'startbot' in sys.argv:
            self.start_bot()

        # Start Discord bot task directly.
        if '_startbot' in sys.argv:
            self._start_bot()

        # Background process method (using nohup)
        if 'stopbot' in sys.argv:
            proc_utils.kill_slime_proc()

        if 'statusbot' in sys.argv:
            proc_utils.status_slime_proc()

        # Show live view of bot log using watch and tail command.
        if 'log' in sys.argv:
            self.show_log()

        # TODO add attach args for server tmux and screen.
        if 'attachbot' in sys.argv:
            self.attach_bot()
        if 'attachserver' in sys.argv:
            self.attach_server()

        # Show help page.
        if 'help' in sys.argv:
            self.script_help()

    def config_prompts(self) -> None:
        """if 'init' variable in configs is False, asks user to setup basic configs."""

        # Creates flatten dict to make it easier to find items to use as defaults
        def get_input(config_promptss):
            new_configs = {}
            for variable, prompt in config_promptss.items():
                parts = prompt.split(':')
                if len(parts) > 1:
                    prompt = parts[1].strip()
                    config_key = parts[0]
                    negate_config = '!' in config_key
                    # Specified config must be false for current prompt to show
                    if negate_config and new_configs.get(config_key.split('!')[1]):
                        continue
                    # Show prompt only if specified config is true.
                    elif not negate_config and not new_configs.get(config_key):
                        continue
                default_value = config.get_config(variable)
                input_type = type(default_value)
                config_input = input(
                    f"{prompt} [{default_value}]: ").strip() or default_value  # Uses default value if enter nothing.
                if input_type is bool:
                    if str(config_input).lower() in ['y', 'yes'] or config_input is True:
                        new_configs[variable] = True
                    if str(config_input).lower() in ['n', 'no']:
                        new_configs[variable] = False
                else:
                    try:
                        new_configs[variable] = input_type(
                            config_input) if input_type else config_input  # Converts to needed type.
                    except:
                        new_configs[variable] = default_value
                        print("Using default:", default_value)
            return new_configs

        # Some questions can be skipped, like how pyenv_activate_command prompt will only show if user says yes to use_pyenv.
        # Add the config with colon, and get_input() will split the prompt and check the prior received inputs. Order of prompts is important.
        # A ! means skip prompt if specified config was answered. E.g. !bot_use_screen will be skipped if bot_use_tmux is True.
        bot_config_promptss = {
            'use_pyenv': "Use Python env (y/n)",
            'pyenv_activate_command': 'use_pyenv: Command to use to activate/source pyenv if using one',
            'bot_token_filepath': "!use_pyenv: Discord bot token filepath",
            'command_prefix': "Discord command prefix",
            'bot_use_tmux': "Run bot using Tmux (y/n)",
            'bot_tmux_name': "bot_use_tmux: Tmux session name for bot",
            'bot_use_screen': "!bot_use_tmux: Run bot using Screen (y/n)",
            'bot_screen_name': 'bot_use_screen: Screen session name for bot',
            'server_files_access': "Let bot access Minecraft server files (y/n)",
            'mc_path': "server_files_access: Path for MC servers and their backups",
        }
        server_config_promptss = {  # Optionally setup server
            'server_name': 'Server name',
            'server_description': 'Server description',
            'server_address': 'Server domain/IP',
            'server_port': 'Server port',
            'server_use_rcon': 'Use RCON (y/n)',
            'rcon_pass': 'server_use_rcon: RCON password',
            'rcon_port': 'server_use_rcon: RCON Port',
            'server_use_tmux': "Run server using Tmux (y/n)",
            'server_tmux_name': "server_use_tmux: Tmux session name for server",
            'server_use_screen': "!server_use_tmux: Run server using Screen (y/n)",
            'server_screen_name': 'server_use_screen: Screen session name for server',
            'server_use_subprocess': "!server_use_tmux: Run server subprocess (y/n)",
        }

        print("----- Config Setup -----\nPress enter to use default.")
        configs = get_input(bot_config_promptss)

        # Asks to continue to server configs
        ask_input = input(f"\nContinue to server config (y/n) [False]: ").strip().lower()
        if ask_input in ['y', 'yes']:
            new_server_config = get_input(server_config_promptss)
            config.new_server_configs(new_server_config['server_name'], new_server_config)

        if mc_path := configs.get('mc_path'):
            config.initialize_configs(mc_path=mc_path)

        config.bot_configs.update(configs)
        config.set_config('init', True)
        config.update_all_configs()  # Updates paths configs, and writes to file.

    def start_bot(self) -> None:
        """Uses different methods of launching Discord bot depending on config"""

        if 'tmux' in self.bot_session:
            if not self.start_bot_tmux():
                return
        elif 'screen' in self.bot_session:
            if not self.start_bot_screen():
                return
        else: self._start_bot()

    def _start_bot(self, launch=None) -> None:
        """Starts Discord bot. This is a separate function incase you want to run the bot inline."""

        # If using virtual environment
        if config.get_config('use_pyenv'):
            # Runs run_bot.py _startbot if not already in venv.
            if sys.prefix == sys.base_prefix:
                subprocess.run(['/home/secr/pyenvs/slime_server/bin/python3', f"{config.get_config('bot_source_path')}/run_bot.py", "_startbot"])
                sys.exit()

        if os.path.isfile(config.get_config('bot_token_filepath')):
            with open(config.get_config('bot_token_filepath'), 'r') as file:
                TOKEN = file.readline()
                lprint(f"INFO: Using Discord Token: {config.get_config('bot_token_filepath')}")
        else:
            lprint(f"ERROR: Missing Token File: {config.get_config('bot_token_filepath')}")
            # TODO use return?
            sys.exit()

        from bot_files.slime_bot import bot
        bot.run(TOKEN, reconnect=True)

    def start_bot_tmux(self) -> bool:
        """Start bot in tmux session."""

        if utils.start_tmux_session(self.tmux_name) is False:
            return False
        
        if os.system(f"tmux send-keys -t {self.tmux} 'cd {config.get_config('bot_source_path')}' ENTER"):
            lprint(f"ERROR: Changing directory {config.get_config('bot_source_path')}")
            return False

        # If using virtual environment
        if config.get_config('use_pyenv'):
            pyenv = config.get_config('pyenv_activate_command')
            if os.system(f"tmux send-keys -t {self.tmux} '{pyenv}' ENTER"):
                lprint(f"ERROR: Couldn't use pyenv: {pyenv}")
                return False
            else: lprint(f"INFO: Activated pyenv: {pyenv}")

        if os.system(f"tmux send-keys -t {self.tmux} '{config.get_config('bot_launch_command')} {self.dev_mode}' ENTER"):
            lprint("ERROR: Could not start bot in tmux.")
            return False
        else: lprint("INFO: Started Discord bot.")

        return True

    def start_bot_screen(self) -> bool:
        """Start bot in screen session."""

        if os.system(f"screen -dmS '{self.screen_name}' {config.get_config('bot_launch_command')}"):
            lprint(f"ERROR: Could not start server with screen: {self.screen_name}")
            return False

        lprint(f"INFO: Started bot in screen session: {self.screen_name}")
        return True

    def attach_bot(self) -> None:
        """Attaches to tmux/screen session containing bot."""

        if 'tmux' in self.bot_session:
            if os.system(f"tmux a -t {self.tmux_name}"):
                lprint(f"ERROR: Unable to attach to tmux session: {self.tmux_name}")
        elif 'screen' in self.bot_session:
            if os.system(f"screen -r {self.screen_name}"):
                lprint(f"ERROR: Unable to attach to screen session {self.screen_name}")

    def attach_server(self) -> None:
        """Attaches to tmux/screen session containing server."""

        if config.get_config('server_use_tmux'):
            if os.system(f"tmux a -t {config.get_config('server_tmux_name')}"):
                lprint(f"ERROR: Unable to attach to tmux session: {self.tmux_name}")
        elif config.get_config('server_use_screen'):
            if os.system(f"screen -r {config.get_config('server_screen_name')}"):
                lprint(f"ERROR: Unable to attach to screen session {self.screen_name}")


    def show_log(self) -> None:
        """Use watch + tail command on bot log."""

        os.system(f"watch -n {watch_interval} tail {config.get_config('bot_log_filepath')}")

    def script_help(self) -> None:
        """Shows help page for run_bot.py"""

        help = """
python3 run_bot.py setup download startboth            --  Create required folders, downloads latest server.jar, and start server and bot with Tmux.
python3 run_bot.py tmuxstart startboth tmuxattach      --  Start Tmux session, start server and bot, then attaches to Tmux session.

help            - Shows this help page.
makefolders     - Create necessary folders. Starts Tmux session in detached mode with 2 panes.
startbot        - Creates tmux or screen session and launches Discord bot.
stopbot         - Stops Discord bot.
attachbot       - Attaches to session containing bot (tmux or screen).
attachserver    - Attaches to session containing server (tmux or screen).
log             - Show bot log using 'watch -n X tail .../bot_log.txt' command. To get out of it, use ctrl + c.
Use standalone, showlog will not work properly if used with other arguments.

NOTE:   The corresponding functions will run in the order you pass arguments in.
For example, 'python3 run_bot.py startbot tmuxattach tmuxstart' won't work because the script will try to start the server and bot in a Tmux session that doesn't exist.
Instead run 'python3 tmuxstart startboth tmuxattach', start Tmux session then start server and bot, then attach to Tmux session.
            """
        print(help)

    def show_banner(self) -> None:
        """Shows banner containing some bot config."""

        # Hides sensitive info from output.
        nono = config.get_config('show_sensitive_info')  # what? got a problem with the naming? it works.
        no = '**********'  # 2bad. change it!

        vars_msg = f"""
NOTE: More config info in README.md or read comments in slime_config.py file in bot_files.
Bot:
Version             {__version__} - {__date__}
Python Env          {config.get_config('pyenv_activate_command') if config.get_config('use_pyenv') else 'None'}
Config File:        {config.get_config('user_config_filepath')}
Bot Log             {config.get_config('bot_log_filepath')}
Tmux                {config.get_config('bot_use_tmux')}
Screen              {config.get_config('bot_use_screen')}
Windows Mode        {config.get_config('windows_compatibility')}

Discord:
Discord Token       {config.get_config('bot_token_filepath')}
Command Prefix      {config.get_config('command_prefix')}
Case Insensitive    {config.get_config('case_insensitive')}
Channel ID          {config.get_config('channel_id') if nono else no}
Show Custom Status  {config.get_config('check_before_command')} - {config.get_config('custom_status_interval')}min
Disabled Commands   {', '.join(config.get_config('disabled_commands'))}
        """

        if config.get_config('bot_use_tmux'): vars_msg += f"""
Bot Tmux:
Name and pane       {self.tmux}
        """

        if config.get_config('bot_use_screen'): vars_msg += f"""
Bot Screen:
Session Name        {config.get_config('bot_screen_name')}
        """

        vars_msg += f"""
Server:
File Access         {config.get_config('server_files_access')}
Autosave            {config.get_config('enable_autosave')} - {config.get_config('autosave_interval')}min
Server URL          {config.get_config('server_address') if nono else no}
Server Port         {config.get_config('server_port') if nono else no}
RCON                {config.get_config('server_use_rcon')}
Tmux                {config.get_config('server_use_tmux')}
Screen              {config.get_config('server_use_screen')}
Subprocess          {config.get_config('server_use_subprocess')}
"""

        if config.get_config('server_use_tmux'): vars_msg += f"""
Server Tmux:        
Name and pane       {config.get_config('server_tmux_name')}:{config.get_config('server_tmux_pane')}
            """

        if config.get_config('server_use_screen'): vars_msg += f"""
Server Screen:
Session Name        {config.get_config('server_screen_name')}
        """

        if config.get_config('server_use_rcon'): vars_msg += f"""
Server RCON:
Pass                {config.get_config('rcon_pass') if nono else no}
Port                {config.get_config('rcon_port') if nono else no}
"""

        if config.get_config('server_files_access'): vars_msg += f"""
Server Paths:
Minecraft Path      {config.get_config('mc_path')}
"""

        print(vars_msg)


if __name__ == '__main__':
    slime = Slime_Bot()
