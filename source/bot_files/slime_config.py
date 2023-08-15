"""
self.bot_configs contain all bot related settings.
self.servers contains configs for each server.
"""

__version__ = '9.0.2 beta'
__date__ = '07/08/2023'
__author__ = 'github.com/0n1udra'
__license__ = 'GPL 3'
__status__ = 'Development'
__discord__ = 'https://discord.gg/s58XgzhE3U'  # Join for bot help (if i'm online :)

import os
import re
import json
import platform
from typing import Union, Any, Dict

import discord


class Config():
    bot_source_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '//')
    # Discord Developer Portal > Applications > Your bot > Bot > Enable 'MESSAGE CONTENT INTENT' Under 'Privileged Gateway Intents'
    intents = discord.Intents.default()  # Default: discord.Intents.default()
    intents.message_content = True  # Default: True

    def __init__(self):

        # Set default variables. (needed before setup_configs() in run_bot.py to allow usage of defaults)
        self.home_path = os.path.expanduser('~').replace('\\', '//')
        self.mc_path = f"{self.home_path}//Games//Minecraft"
        self.bot_configs = {}
        self.servers = {'example': {}}
        self.initialize_configs()
        self.initial_example_configs = {}
        self.example_server_configs = self.servers['example']
        self.server_configs = self.servers['example']  # Will be updated with currently selected server
        self.server_name = self.server_configs['server_name']

    def initialize_configs(self, mc_path: str = None) -> None:
        """Initiates config with correct data and paths, optionally use data from setup_configs() from run_bot.py"""

        if mc_path: self.mc_path = mc_path

        self.bot_configs = {
            # Use python virtual environment
            'use_pyenv': False,
            'pyenv_activate_command': f'source {self.home_path}//pyenvs//slime_server//bin//activate',
            # How run_bot.py script launches the Discord bot.
            'bot_launch_command': "python3 run_bot.py _startbot",
            # Shows sensitive info in bot launch output. Discord token, Server URL, RCON Data, etc...
            'show_sensitive_info': False,

            # ===== Discord config
            # Set location of Discord bot token using double back slashes '//'
            # Get Discord bot token at: https://discord.com/developers/applications
            'bot_token_filepath': f'{self.home_path}//keys//slime_bot.token',
            'command_prefix': '?',
            # Case insensitivity for discord commands. e.g. ?players, ?Players, ?pLaYers will be the same.
            'case_insensitive': True,
            # Can use ?setchannel command or set here, it's to send a startup message in Discord.
            'channel_id': 0,
            # Every X minutes, updates bot's custom status showing player's online and server ping. E.g. Playing - 3 | Ping - 10
            # NOTE: Need to set 'enable-query=true' in server.properties for this to work. Tip: '?property enable-query true'
            'players_custom_status': True,
            'custom_status_interval': 1,

            # Use Tmux to send commands to server.
            'bot_use_tmux': False,
            'bot_tmux_name': 'slime_bot',
            'bot_tmux_pane': '0.0',

            # Use Screen to run bot. NOTE: Tmux takes priority of both are set to True.
            'bot_use_screen': False,
            'bot_screen_name': 'slime_bot',

            # If editing these paths, make sure the 'example' server defaults are updated aswell.
            'home_path': self.home_path,
            'bot_source_path': self.bot_source_path,
            'mc_path': self.mc_path,
            'servers_path': f'{self.mc_path}//servers',
            'user_config_filepath': f'{self.bot_source_path}//user_config.json',
            'bot_filepath': f'{self.bot_source_path}//bot_files',
            'bot_log_filepath': f'{self.bot_source_path}//slime_bot.log',

            # Use cmd commands. E.g. 'start' command when starting a server only if platform.systems() == 'Windows'.
            'windows_compatibility': True if platform.system() == 'Windows' else False,
            # Will be prefixed to server_launch_command in server_start() func to be windows compatible.
            'windows_cmdline_start': 'start "Minecraft server"',

            'selected_server': 'example',
            'init': False,
        }

        self.servers = {
            'example': {  # has to be the same as the server_name key within.
                'server_name': 'example',
                'server_description': 'example server used as template',

                # For compatibility. e.g. From 1.12 to 1.13+ the /list command output is different, /data get entity doesn't work, etc...
                'server_version': None,

                # Server domain or IP address. Used for server_ping(), ping_address(), etc,.
                'server_address': 'localhost',  # Leave '' for blank instead of None or False
                'server_port': 25565,
                # Will be updated by get_public_ip() function in backend_functions.py on bot startup.
                'server_ip': 'localhost',

                # Local file access allows for server files/folders manipulation,for features like backup/restore world saves, editing server.properties file, and read server log.
                'server_files_access': False,

                # Use tmux to run/command Miencraft server.
                'server_use_tmux': False,
                'server_tmux_name': 'slime_server',
                # Tmux pane for minecraft server if using Tmux.
                'server_tmux_pane': '0.1',
                
                # Use screen to start and send commands to Minecraft server. Only Minecraft server, bot can be run alone or in tmux.
                'server_use_screen': False,
                'server_screen_name': 'minecraft_server',

                # Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halt also.
                # Useful if you can't use Tmux. Prioritizes server_use_subprocess over Tmux option for commands like ?serverstart.
                'server_use_subprocess': False,

                # Launch command to start Minecraft java server.
                'server_launch_command': 'java -server -Xmx4G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2 -jar server.jar nogui',
                # Set a custom path where to launch server. Set to None to use default.
                'server_launch_path': None,

                # Use RCON to send commands to server. You won't be able to use some features like reading server logs.
                'server_use_rcon': False,
                'rcon_pass': 'pass',
                'rcon_port': 25575,

                # Second to wait before checking status for ?serverstart. e.g. PaperMC ~10s (w/ decent hardware), Vanilla ~20, Valhesia Volatile ~40-50s.
                'startup_wait_time': 30,
                # How much time to give server after using 'save-all' command.
                'save_world_wait_time': 3,

                # Only send command after sending unique number to console to check status.
                'check_before_command': True,
                # The command sent to server to check if responsive. send_command() will send something like 'xp 0.64356...'.
                'status_checker_command': 'xp',
                # Wait time (in seconds) between sending command to MC server and reading server logs for output.
                # Time between receiving command and logging output varies depending on PC specs, MC server type (papermc, vanilla, forge, etc), and how many mods.
                'command_buffer_time': 1,

                # TODO Fix
                # Send 'save-all' to MC server every X minutes.
                'enable_autosave': False,
                'autosave_interval': 60,

                # Max number of log lines to read. Increase if server is really busy.
                'log_lines_limit': 500,

                # SELECTED_SERVER will be substituted with server name.
                'server_path': f'{self.mc_path}//servers//SELECTED_SERVER',
                'world_backups_path': f'{self.mc_path}//world_backups//SELECTED_SERVER',
                'server_backups_path': f'{self.mc_path}//server_backups//SELECTED_SERVER',
                'server_logs_path': f'{self.mc_path}//servers//SELECTED_SERVER//logs',
                'server_log_filepath': f'{self.mc_path}//servers//SELECTED_SERVER//logs//latest.log',
                'server_properties_filepath': f'{self.mc_path}//servers//SELECTED_SERVER//server.properties',

                # For '?links' command. Shows useful websites.
                'useful_websites': {
                    'Minecraft Download': 'https://www.minecraft.net/en-us/download',
                    'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                    'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                    'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                },
            }
        }

        self.update_variables()

    def update_variables(self) -> None:
        """Update needed instance variables, and also adds any newly added server configs."""

        self.example_server_configs = self.servers['example']
        self.server_configs = self.servers['example']  # Will be updated with currently selected server
        self.server_name = self.server_configs['server_name']

    def get_config(self, config_key: str, default_return: Any = None) -> Union[Any, None]:
        """
        Get config from bot configs or selected server configs.

        Args:
            config_key str: Config to get.
            default_return Any: What to return if not found.

        Returns:
            Any, None: Returns config value or None if not found.
        """

        return self.bot_configs.get(config_key, self.server_configs.get(config_key, default_return))

    def set_config(self, key: str, value: Any) -> bool:
        """
        Updates bot or server config. Only if config already exists.

        Args:
            key: Config to edit.
            value: New value.

        Returns:
            bool: If update successful.
        """

        if key in self.bot_configs:
            self.bot_configs[key] = value
        elif key in self.server_configs:
            self.servers[self.server_name][key] = value
        else:
            return False

        self.update_all_configs()
        self.switch_server_configs(self.server_name)  # Updates instance variables.
        return True

    def _update_config_paths(self, config_data: Dict, server_name: str = None, text_to_replace: str = 'SELECTED_SERVER') -> Dict:
        """
        Updates the paths variables in the configs with correct path and format.
        Replaces any singular slash with double for linux and windows compatibility.
        Example:
        "server_path": "/home/0n1udra/Games/Minecraft/servers/SELECTED_SERVER"
        into
        "server_path": "//home//0n1udra//Games//Minecraft//servers//papermc",

        Args:
            server_name str: Name of server to update data with.
            config_data str('SELECTED_SERVER'): What section of the paths to replace.

        Returns:
            dict: An updated dictionary.
        """

        config_data = config_data.copy()
        for k, v in config_data.items():
            if 'path' in k and isinstance(v, str):  # Replaces SELECTED_SERVER only if key has 'path' in it.
                # Makes sure all paths uses double slashes '//' for windows and linux compatibility
                v = re.sub(r'(?<!/)/(?![/])', '//', v).replace('\\', '//')
                v = re.sub(r'/+', '//', v)
                if v.endswith('//'): v = v[:-2]
                if server_name and config_data['server_name'] != 'example':
                    v = v.replace(text_to_replace, server_name)
                config_data[k] = v

            # Turns anything that contains only numbers to integer format.
            if str(v).isnumeric() and 'pass' not in k:
                config_data[k] = int(v)

        return config_data

    def update_all_configs(self) -> None:
        """Checks if there's new configs in 'example' and updates the other servers with defaults."""

        for server_name, server_configs in self.servers.items():
            new_server_configs = self.example_server_configs.copy()
            new_server_configs.update(server_configs)  # Updates example template values with user set ones, fallback on 'example' defaults
            # Updates paths variables that contain 'SELECTED_SERVER' with server's name
            self.servers[server_name] = self._update_config_paths(new_server_configs, server_name)

        self.bot_configs = self._update_config_paths(self.bot_configs)

        self.update_configs_file()

    def new_server_configs(self, server_name: str, config_data: Dict = None) -> Union[Dict, bool]:
        """
        New server configs.

        Args:
            server_name: Name of new server.
            config_data: Config dict.

        Returns:
            dict, bool: Dict of new configs. False if error.
        """

        if server_name in self.servers:
            return False

        self.servers[server_name] = config_data.copy() if config_data else self.example_server_configs.copy()
        self.servers[server_name]['server_name'] = server_name
        # Adds default configs for the ones not set, and updates config json file.
        self.update_all_configs()
        return self.servers[server_name]

    def update_server_configs(self, server_name: str, new_data: Dict) -> Union[Dict, bool]:
        """
        Updates server configs.

        Args:
            server_name str: Name of server to edit.
            new_data dict: Updated server configs dict.

        Returns:
            dict, bool: Updated server configs dict, or False if no configs exists.
        """

        # Makes this function only for updating configs. If configs not exist, must use new_server_configs()
        if server_name not in self.servers:
            return False

        server_configs = self.example_server_configs.copy()
        # Gets any preexisting data.
        if server_name in self.servers:
            server_configs.update(self.servers[server_name])
        server_configs.update(new_data)  # Updates example template values with user set ones, fallback on 'example' defaults
        new_server_name = server_configs['server_name']
        # Updates paths variables with new server name, e.g. ../servers/old_name/ > ../servers/new_name/
        self.servers[new_server_name] = self._update_config_paths(server_configs, new_server_name, server_name)

        self.servers.pop(server_name)  # Delete old server configs
        self.update_configs_file()

        return server_configs

    def update_from_file(self) -> bool:
        """Updates configs from config json file."""

        if not os.path.isfile(self.get_config('user_config_filepath')):
            return False

        # Updates bot_config sub-dict. This will preserve manually added variables. It will add defaults of missing needed configs
        with open(self.get_config('user_config_filepath'), 'r') as openfile:
            try: json_data = json.load(openfile)
            except: return False
            self.bot_configs.update(json_data['bot_configs'])
            self.servers.update(json_data['servers'])
            # Adds any newly added configs to servers.
            self.servers['example'].update(self.example_server_configs)
            self.update_variables()
            # This will also call update_config_file() which will write to user_config.json
            self.switch_server_configs(self.bot_configs['selected_server'])
        return True

    def update_configs_file(self) -> bool:
        """
        Write self.bot_configs and self.servers to json file.

        Returns:
            bool: If successful.
        """

        from bot_files.slime_utils import file_utils
        file_data = file_utils.write_json(self.get_config('user_config_filepath'),
                                          {'bot_configs': self.bot_configs, 'servers': self.servers})
        if not file_data:
            return False

        return True

    def switch_server_configs(self, server_name: str) -> bool:
        """
        Switches server_configs with correct configs.

        Args:
            server_name: Name of server to select.

        Returns:
            bool: True if server config found and set. False if no server configs found.
        """

        if server_configs := self.servers.get(server_name, None):
            self.server_configs = server_configs
            self.server_name = self.bot_configs['selected_server'] = server_name
            self.update_configs_file()
            return True
        return False


config = Config()
config.initialize_configs()