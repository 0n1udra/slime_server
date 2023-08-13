"""
Handles which server API to use depending on configs, managing world/server backups, reading and managing server files.

Project Structure:
    Objects:
        Backend - slime_backend.py, Server start/stop, world/server backups, sending commands, reading/managing server files.
            Server_API - slime_api.py, Sending commands and reading log output.
        Comps - discord_components.py, Anything relating to discord component and embeds.
        Bot - slime_bot.py, Discord bot.
        Utils, File_utils - slime_utils.py, Useful utilities like parsing input and formatting outputs, etc.
    Cogs:
        backups.py, Server/world backup management
        player.py, Common player commands and controls like: banning, whitelist, gamemode, etc
        server.py, Server status, start/stop, editing properties, managing different servers.
        world.py, Game related and world relating stuff, like say, chat log, weather, time, etc.
"""

import os
import fileinput
from os.path import join
from typing import Union, Dict, Tuple, List

from discord.ext.commands import Bot, Context
import mctools

from bot_files.server_api import Server_API, Server_API_Screen, Server_API_Subprocess, Server_API_Rcon, Server_API_Tmux
from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils, file_utils

class Backend():
    # The order of this dictionary determines the priority of which API to use if multiple are enabled in configs.
    server_api_types = {
        'server_use_rcon': Server_API_Rcon,
        'server_use_screen': Server_API_Screen,
        'use_tmux': Server_API_Tmux
    }

    def __init__(self):
        # Specific API for server interaction depending on server type (vanilla, PaperMC, etc) .
        self.bot = None
        self.messages = []
        self.last_command_channel_id = None
        self.server_api = None
        self.subprocess_servers = {}
        self.discord_channel = None
        self.server_active = False
        config.update_from_file()  # Reads from json config file if exists.

    # ===== Discord
    async def update_bot_object(self, bot: Bot) -> bool:
        """
        Update's Discord bot object in Backend, also tries updating discord_channel.

        Args:
            bot: Discord bot object.

        Returns:
            bool: If successful.
        """

        if isinstance(bot, Bot):
            self.bot = bot
            self.set_discord_channel()
            await self.select_server(config.get_config('selected_server'))
            self.server_api.bot = bot
            return True

        return False

    def set_discord_channel(self, ctx: Context = None) -> bool:
        """
        Updates discord_channel with Discord channel object wtih channel_id config, so you can use send_channel_msg func.

        Args:
            bot: Needs discord.ext.commands.bot object to send message to find channel by ID.

        Returns:
            bool: Successfully found Discord chanel by set channel_id config.
        """

        # Needs bot object to get discord channel from channel id.
        if self.bot is None:
            return False
        # Gets channel id from message ctx object.
        if isinstance(ctx, Context):
            channel_id = ctx.channel.id
        # Checks if channel_id is set.
        elif channel_id := config.get_config('channel_id'):
            channel_id = channel_id

        # Only updates data if new channel_id received
        if self.last_command_channel_id != channel_id:
            self.last_command_channel_id = channel_id
            config.set_config("channel_id", channel_id)
            self.discord_channel = self.bot.get_channel(channel_id)

        return True

    async def send_msg(self, *args, **kwargs) -> bool:
        """

        Args:
            msg:

        Returns:

        """

        if self.discord_channel is None:
            return False

        msg = await self.discord_channel.send(*args, **kwargs)
        self.messages.append(msg)
        return msg

    async def clear_messages(self, clear_comps=False) -> None:
        """

        Args:
            clear_comps:

        Returns:

        """

        for msg in self.messages:
            try: await msg.delete()
            except: pass

    # ===== Server API
    async def select_server(self, server_name: str) -> bool:
        """
        Updates relevant server command functions and configs.

        Args:
            server_name: Server to select.

        Returns:
            bool: Successful switch.
        """

        if config.switch_server_configs(server_name) is False:
            return False

        # In cases of wanting to use subprocess to run Minecraft server and have the ability to switch servers to control.
        # This needs its own object so you can switch between them without killing the Minecraft server subprocess.
        if config.get_config('server_use_subprocess'):
            server_name = config.server_configs['server_name']
            # Checks if a subprocess API instance for selected server already exists.
            if config.server_configs['server_name'] in self.subprocess_servers:
                return self.subprocess_servers[server_name]
            else:
                # Create new subprocess API
                new_subprocess_server = Server_API_Subprocess()
                self.subprocess_servers[server_name] = new_subprocess_server
                self.server_api = new_subprocess_server
                return True

        for config_name, api in self.server_api_types.items():
            # Checks if corresponding config is enabled to use API, e.g. use_rcon, use_tmux, use_screen, etc...
            if config.get_config(config_name):
                self.server_api = api()  # Set server_api to correct API (Server_API_Tmux, Server_API_Rcon, etc).
                break

        if not self.server_api:
            self.server_api = Server_API()

        lprint(f"INFO: Selected Server: {server_name}")
        return True

    # Send command to server console.
    async def send_command(self, command: str) -> bool:
        """
        Sends command to Minecraft server. Depending on whether server is a subprocess or in Tmux session or using RCON.
        Sends command to server, then reads from latest.log file for output.
        If using RCON, will only return RCON returned data, can't read from server log.

        Args:
            command str: Command to send.

        Returns:
            bool: If successfully sent command to console.
        """

        # check_before_command is False, the bot will send the server commands even if status of server status is unknown.
        # Skips this if no local file access.
        if config.get_config('check_before_command') and config.get_config('server_files_access'):
            if not await self.server_api.server_console_reachable():
                return False

        if await self.server_api.send_command(command):
            self.server_api.last_command_sent = command
            return True

        return False

    async def get_command_output(self, keywords: str = None, extra_lines: int = 0, all_lines=False) -> Union[str, bool]:
        """

        Returns:

        """

        return await self.server_api.get_command_output(keywords, extra_lines, extra_lines, all_lines)

    # ===== Server status
    # Checks if server is reachable. By sending a command or using ping, depending on configs.
    async def server_status(self, force_check: bool = False) -> bool:
        """
        Returns boolean if server is active.
        Depending on configs, priority: ping_server(), server_console_reachable(), _get_status()

        Returns:
            bool: If server is active (not always same as MC console is reachable).
        """

        # Can force check even if configs disable it.
        if config.get_config('check_before_command') or force_check:
            return await self.server_api.server_console_reachable()

        return await self.server_ping()

    async def server_ping(self) -> Union[str, bool]:
        """
        Uses ping command to check if server reachable.

        Returns:
            bool: If ping was successful.
        """

        if data := await self.server_ping_query():
            return round(data['time'], 2)
        if address := config.get_config('server_address'):
            return await utils.ping_address(address)

        return False

    # Query ping server. Must have 'enable-query=true' in server.properties.
    async def server_ping_query(self) -> Union[Dict, bool]:
        """
        Gets server information using mctools.PINGClient()

        Returns:
            dict: Dictionary containing 'version', and 'description' (motd).
        """

        if not config.get_config('server_address'):
            await self.send_msg("**Error:** Could not query server address.")
            lprint("ERROR: Could not query server address.")
            return False
        if not config.get_config('server_port'):
            await self.send_msg("**Error:** Server port issue.")
            lprint("ERROR: Server port issue.")
            return False

        try:
            ping = mctools.PINGClient(config.get_config('server_address'), config.get_config('server_port'))
            stats = ping.get_stats()
            ping.stop()
        except:
            return False
        else:
            return stats

    # ===== Get data
    async def get_players(self) -> Union[Tuple[List[str], str], bool]:
        """
        Extracts wanted data from output of 'list' command.

        Returns:
            Player data, bool: Returns player names and associating text, or False.
        """

        # Converts server version to usable int. Extracts number after initial '1.', e.g. '1.12.2' > 12
        version = await self.get_server_version()  # Needs version to know how to parse output.
        response = await self.send_command("list")

        if not response:
            await self.send_msg("**Error:** No response from console.")
            lprint("ERROR: Unable to fetch player list, no response from console.")
            return False
        if not version:
            await backend.send_msg("**Error:** Unable to get server version.")
            lprint("ERROR: Unable to fetch player list, problem getting server version.")
            return False

        output = await backend.get_command_output('There are', 1)
        return utils.parse_players_output(output, version)

    async def get_coords(self, player: str = '') -> Union[str, bool]:
        """Gets player's location coordinates."""

        if not await backend.send_command(f"data get entity {player} Pos"):
            return False
            #log_data = self.read_server_log('entity data', stopgap_str=response[1])
        # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
        # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
        if log_data := await self.get_command_output('data get entity'):
            location = log_data.split('[')[-1][:-3].replace('d', '')
            return location

    async def get_motd(self) -> str:
        """
        Returns the server's Message of the day.

        Returns:
            str: MoTD, or N/A if not found.
        """

        if data := await self.get_property('motd'):
            msg = str(data).split('=')[-1]
        else: msg = 'N/A'

        lprint(f"INFO: Fetching MoTD: {msg}")
        return msg

    async def get_server_version(self, force_check=False) -> Union[str, bool]:
        """
        Gets server version number.

        Returns:
            str, bool: Server version. Or False if not found.
        """

        version = None

        # Check if config has version already. Some commands (?version, etc) will force bot to check server version.
        from_config = config.get_config('server_version')
        if not force_check and from_config:
            return from_config

        if config.get_config('server_files_access'):
            # Tries to find version info from latest.log.
            if data := await self.read_server_log('server version', top_down_mode=True):
                version = data[0].split('version')[-1].strip()
            # Tries to find info in server.properties next.
            elif data := await self.get_property('version'):
                version = data

        # Get version info from server console.
        elif await self.send_command('version'):
            if data := await self.get_command_output('This server is running'):
                version = utils.parse_version_output(data[0])

        # Fallback to version from config file.
        version = version or from_config
        # Only update if different version.
        if version and version != config.get_config('server_version'):
            config.set_config('server_version', version)

        return version if version else False

    # ===== File reading and writing
    # TODO Make async
    async def read_server_log(self, *args, **kwargs):
        if not config.get_config('server_files_access'):
            return False

        return await self.server_api.read_server_log(*args, **kwargs)

    async def update_property(self, property_name=None, value: str = '') -> Union[str, bool]:
        """
        Edits server.properties file if received target_property and value. Edits inplace with fileinput
        If receive no value, will return current set value if property exists.

        Args:
            property_name str(None): Find Minecraft server property.
            value str(''): If received argument, will change value.

        Returns:
            str: If target_property returns line from file.
            bool: Returns False if property not found.
        """

        if not config.get_config('server_files_access'):
            return False

        file_path = config.get_config('server_properties_filepath')
        if not file_utils.test_file(file_path):
            return False

        # print() writes to file while using it in FileInput() with inplace=True
        # fileinput doc: https://docs.python.org/3/library/fileinput.html
        return_line = None
        with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
            for line in file:
                split_line = line.split('=', 1)  # E.g. enable-rcon=true
                if property_name in split_line[0] and len(split_line) > 1:
                    if value:
                        line = '='.join([split_line[0], value])
                    # If user did not pass a new value to update property, just return the line from file.
                    return_line = line.strip()
                print(line, end='')

        # Returns value, and complete line
        return return_line if return_line else False

    async def get_property(self, property_name: str) -> Union[str, bool]:
        """
        Get a property from server properties file.

        Args:
            property_name str: Property name to get.

        Returns:
            str: Value found.
            bool: If value not found or if not able to access file.
        """

        if config.get_config('server_files_access'):
            if data := await self.update_property(property_name):
                return data

        return False

    # ===== Adding/Deleting servers
    async def server_new(self, server_name: str, server_data: Dict = None, new_folder=True) -> Union[Dict, bool]:
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            server_name str: Name of new server.

        Returns:
            dict, bool: Dictionary of new server configs or False if failed.
        """

        # Checks if server configs already exists.
        if server_name in config.servers:
            lprint(f"ERROR: Can't create new server, configs already exists for: {server_name}")
            return False

        # Create new configs for server.
        server_data = config.new_server_configs(server_name, server_data)
        if not server_data:
            lprint(f"ERROR: Issue creating new configs for: {server_name}")
            return False

        # Create new folder for server.
        if new_folder and not os.path.isdir(server_data['server_path']):
            if not file_utils.new_dir(server_data['server_path']):
                return False

        return server_data

    async def server_delete(self, server_name: str) -> Union[Dict, bool]:
        """

        Args:
            server_name:

        Returns:
            dict, bool:
        """

        if server_name not in config.servers:
            return False

        if not file_utils.delete_dir(config.servers[server_name]['server_path']):
            return False

        server_data = config.servers.pop(server_name)
        config.update_configs_file()
        return server_data

    async def server_edit(self, server_name: str, new_server_data: Dict) -> bool:
        """
        Edit existing server configs. Also renames folder if name changed.

        Args:
            server_name str: Server name to edit.
            server_data dict: New server configs.

        Returns:
            bool: If update successful.
        """

        # Updates folder name if name changed.
        if server_name != new_server_data['server_name']:
            original_path = config.servers[server_name]['server_path']
            new_path = join(config.get_config('servers_path'), new_server_data['server_name'])
            if os.path.isdir(original_path) is False:
                return False

            try: os.rename(original_path, new_path)
            except:
                return False
            lprint(f"Renamed server folder: {original_path} > {new_path}")

        # Updates server configs.
        if config.update_server_configs(server_name, new_server_data):
            lprint(f"Updated server configs: {server_name}")
            return True

        return False

    async def server_copy(self, server_name: str, new_server_name: str) -> Union[Dict, bool]:
        """

        Args:
            server_name:
            new_server_name:

        Returns:

        """

        if new_server := await self.server_new(new_server_name, new_folder=False):
            if file_utils.copy_dir(config.servers[server_name]['server_path'], new_server['server_path']) is False:
                return False
            else:
                return new_server
        return False

    # ===== Backup/Restore
    async def new_backup(self, new_name, mode: str) -> Union[str, bool]:
        """
        Create a new world or server backup, by copying all folders with 'world_' in its name.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.

        Returns:
            str, bool: If success, returns name path of backup, else False if error happens.
        """

        # Creates folder name, date, version, optional keywords
        version = await self.get_server_version()
        version_text = f"{f'v({version}) ' if version else ''}"
        new_name = f"({utils.get_datetime()}) {version_text}{new_name}"
        # E.g. (2023-08-03 16-29) v(1.19.4) test backup

        # Copies whole server folder.
        if 'server' in mode:
            new_backup_path = join(config.get_config('server_backups_path'), new_name.strip())
            source_path = config.get_config('server_path')
            if file_utils.copy_dir(source_path, new_backup_path) is False:
                return False

        # Copies all folders containing 'world' in name. I.e. world, world_nether, world_the_end
        elif 'world' in mode:
            new_backup_path = join(config.get_config('world_backups_path'), new_name.strip())
            error = False
            for folder in os.listdir(config.get_config('server_path')):
                if 'world' in folder:
                    if file_utils.copy_dir(join(config.get_config('server_path'), folder), join(new_backup_path, folder)) is False:
                        error = True  # Even if failed, try to backup the others.

            if error:
                return False

        return new_name

    async def restore_backup(self, src, dst) -> bool:
        """
        Restores world or server backup. Overwrites existing files.

        Args:
            src str: Backed up folder to copy to current server.
            dst str: Location to copy backup to.
        """

        if file_utils.delete_dir(dst):
            if file_utils.copy_dir(src, dst):
                return True

        return False



backend = Backend()
