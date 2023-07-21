import discord, getpass, os, json
from os.path import join

__version__ = '9.0'
__date__ = '19/07/2023'
__author__ = 'github.com/0n1udra'
__license__ = 'GPL 3'
__status__ = 'Development'
__discord__ = 'https://discord.gg/s58XgzhE3U'  # Join for bot help (if i'm online :)

class Config():
    bot_src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Discord Developer Portal > Applications > Your bot > Bot > Enable 'MESSAGE CONTENT INTENT' Under 'Privileged Gateway Intents'
    intents = discord.Intents.default()  # Default: discord.Intents.default()
    intents.message_content = True  # Default: True

    def __init__(self):
        # Set default variables. (needed before setup_configs() in run_bot.py to allow usage of defaults)
        self.configs = {'bot_configs': {}, 'servers': {'example': {}}}
        self.initialize_configs()

        # Some shortcuts
        self.bot_configs = self.configs['bot_configs']
        self.servers = self.configs['servers']
        self.example_server_configs = self.servers['example']
        self.server_configs = self.example_server_configs  # Will be updated with currently selected server

    def initialize_configs(self, configs_from_setup=None):
        """Initiates config with correct data and paths, optionally use data from setup_configs() from run_bot.py"""

        #Gets username to use in paths
        try: self.user = os.getlogin()
        except: self.user = getpass.getuser()
        if not self.user:
            print("ERROR: Need to set 'user' variable in slime_vars.py")
            exit()

        # Get configs from run_bot.py setup_configs()
        if configs_from_setup:
            self.mc_path = configs_from_setup['mc_path']
            self.home_path = configs_from_setup['home_path']
        else:
            self.mc_path = join(os.path.expanduser('~'), 'Games', 'Minecraft')
            self.home_path = os.path.expanduser('~')
            
        self.configs = {
            'bot_configs': {
                # Use python virtual environment
                'use_pyenv': True,
                'pyenv_activate_command': f'source /home/{self.user}/pyenvs/slime_server/bin/activate',
                # How run_bot.py script launches the Discord bot.
                'bot_launch_command': "python3 run_bot.py _startbot",
                # Shows sensitive info in bot launch output. Discord token, Server URL, RCON Data, etc...
                'show_sensitive_info': False,

                # ===== Discord config
                # Set location of Discord bot token using os.path.join. e.g. join(home_dir, 'keys', 'slime_bot.token')
                # Get Discord bot token at: https://discord.com/developers/applications
                'bot_token_filepath': join(self.home_path, 'keys', 'slime_bot.token'),
                'command_prefix': '?',
                # Case insensitivity for discord commands. e.g. ?players, ?Players, ?pLaYers will be the same.
                'case_insensitive': True,
                # Can use ?setchannel command or set here, it's to send a startup message in Discord.
                'channel_id': 0,
                # Every X minutes, updates bot's custom status showing player's online and server ping. E.g. Playing - 3 | Ping - 10
                # NOTE: Need to set 'enable-query=true' in server.properties for this to work. Tip: '?property enable-query true'
                'enable_players_custom_status': True,
                'custom_status_interval': 1,

                # Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
                'use_tmux': True,
                'tmux_session_name': 'slime_server',
                'tmux_bot_pane': '0.0',
                'tmux_minecraft_pane': '0.1',

                # If editing these paths, make sure the 'example' server defaults are updated aswell.
                'mc_path': self.mc_path,
                'servers_path': join(self.mc_path, 'servers'),
                'user_config_filepath': join(self.bot_src_path, 'user_config.json'),
                'bot_filepath': join(self.bot_src_path, 'bot_files'),
                'bot_log_filepath': join(self.bot_src_path, 'slime_bot.log'),

                # Use cmd 'start' command when starting a server only if platform.systems() == 'Windows'.
                'windows_compatibility': True,
                # Will be prefixed to server_launch_command in server_start() func to be windows compatible.
                'windows_cmdline_start': 'start "Minecraft server"',

                'selected_server': 'example',
            },
            'servers': {
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
                    'server_files_access': True,
                    # Use screen to start and send commands to Minecraft server. Only Minecraft server, bot can be run alone or in tmux.
                    'server_use_screen': False,
                    'screen_session_name': 'minecraft_server',
                    # Uses subprocess.Popen() to run Minecraft server and send commands. If this bot halts, server will halt also.
                    # Useful if you can't use Tmux. Prioritizes server_use_subprocess over Tmux option for commands like ?serverstart.
                    'server_use_subprocess': False,
                    # Launch command to start Minecraft java server.
                    'server_launch_command': 'java -server -Xmx4G -Xms1G -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -XX:ParallelGCThreads=2 -jar server.jar nogui',

                    # Use RCON to send commands to server. You won't be able to use some features like reading server logs.
                    'server_use_rcon': False,
                    'rcon_pass': 'pass',
                    'rcon_port': 25575,

                    # Second to wait before checking status for ?serverstart. e.g. PaperMC ~10s (w/ decent hardware), Vanilla ~20, Valhesia Volatile ~40-50s.
                    'startup_wait_time': 30,

                    # Set to False to disable sending 'xp' command to server. NOTE: You won't get for some commands you won't get feedback on success/status.
                    'enable_status_checker': True,
                    # The command sent to server to check if responsive. send_command() will send something like 'xp 0.64356...'.
                    'status_checker_command': 'xp',
                    # Enabling this sends a ping to server before sending command to see if active.
                    # NOTE: This will disable and override 'enable_status_checker'. You can use this if you can't use that.
                    'enable_ping_before_command': False,
                    # Wait time (in seconds) between sending command to MC server and reading server logs for output.
                    # Time between receiving command and logging output varies depending on PC specs, MC server type (papermc, vanilla, forge, etc), and how many mods.
                    'command_buffer_time': 1,

                    # TODO Fix
                    # Send 'save-all' to MC server every X minutes.
                    'enable_autosave': False,
                    'autosave_interval': 60,

                    # Max number of log lines to read. Increase if server is really busy.
                    'log_lines_limit': 500,

                    # Set to True to backup 'world' folder only, exclude folders like 'world_nether', etc...
                    'exact_world_foldername': False,

                    # SELECTED_SERVER will be substituted with server name.
                    'server_path': join(self.mc_path, 'servers', 'SELECTED_SERVER'),
                    "world_backups_path": join(self.mc_path, 'world_backups', 'SELECTED_SERVER'),
                    "server_backups_path": join(self.mc_path, 'server_backups', 'SELECTED_SERVER'),
                    "server_logs_path": join(self.mc_path, 'servers', 'SELECTED_SERVER', 'logs'),
                    "server_log_filepath": join(self.mc_path, 'servers', 'SELECTED_SERVER', 'logs', 'latest.log'),
                    "server_properties_filepath": join(self.mc_path, 'servers', 'SELECTED_SERVER', 'server.properties'),

                    # For '?links' command. Shows useful websites.
                    'useful_websites': {
                        'Minecraft Download': 'https://www.minecraft.net/en-us/download',
                        'Modern HD Resource Pack': 'https://minecraftred.com/modern-hd-resource-pack/',
                        'Minecraft Server Commands': 'https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                        'Minecraft /gamerule Commands': 'https://minecraft.gamepedia.com/Game_rule',
                    }
                }
            }
        }

    def update_server_configs(self):
        """Checks if there's new configs in 'example' and updates the other servers with defaults."""
        global slime_vars
        for server_name, server_configs in slime_vars.servers.items():
            if 'example' in server_name: continue  # Skip example template
            server_configs = self.example_server_configs.copy()
            server_configs.update(server_configs)  # Updates example template values with user set ones, fallback on 'example' defaults

            # Updates paths variables that contain 'SELECTED_SERVER' with server's name
            text_to_replace = 'SELECTED_SERVER'
            server_configs['server_name'] = server_name
            for k, v in server_configs.items():
                if 'path' in k:  # Replaces SELECTED_SERVER only if key has 'path' in it.
                    server_configs[k] = v.replace(text_to_replace, server_name)

            # Updates slime_vars then writes to file.
            #slime_vars.servers.update({name: server})
            #slime_vars.update_vars(slime_vars.config)

    def update_server_paths(server_dict, server_name, text_to_replace=None):
        """
        Replaces 'SELECTED_SERVER' in server dict values if key has 'path' in it.
        """
        text_to_replace = 'SELECTED_SERVER'
        server_dict['server_name'] = server_name
        for k, v in server_dict.items():
            if 'path' in k:  # Replaces SELECTED_SERVER only if key has 'path' in it.
                server_dict[k] = v.replace(text_to_replace, server_name)

        return server_dict


    def update_servers_vars():
        """Checks if there's new configs in 'example' and updates the other servers with defaults."""
        global slime_vars
        for name, data in config.servers.items():
            if 'example' in name: continue  # Skip example template
            server = config.servers['example'].copy()
            server.update(data)  # Updates example template values with user set ones, fallback on 'example' defaults
            server = update_server_paths(server, name)  # Updates paths (substitutes SELECTED_SERVER)
            # Updates slime_vars then writes to file.
            slime_vars.servers.update({name: server})
            slime_vars.update_vars(slime_vars.config)

    def update_from_user_config(config):
        # Updates bot_config sub-dict. This will preserve manually added variables. It will add defaults of missing needed configs
        with open(slime_vars.user_config_filepath, 'r') as openfile:
            def deep_update(original_dict, update_dict):
                for key, value in update_dict.items():  # Updates nested dictionaries.
                    if isinstance(value, dict) and key in original_dict and isinstance(original_dict[key], dict):
                        deep_update(original_dict[key], value)
                    else: original_dict[key] = value
            deep_update(config, json.load(openfile))
        return config


print("OK")
config = Config()
print("OK")
config.initialize_configs()
print("OK")
print(config.configs)