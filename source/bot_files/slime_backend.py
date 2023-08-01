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
from typing import Union, Dict

import discord.ext.commands
from discord.ext.commands import Bot, Context
import mctools

from bot_files.server_api import Server_API, Server_API_Screen, Server_API_Subprocess, Server_API_Rcon, Server_API_Tmux
from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils, file_utils

class Backups:
    pass

class Backend(Backups):
    # The order of this dictionary determines the priority of which API to use if multiple are enabled in configs.
    server_api_types = {
        'use_rcon': Server_API_Rcon,
        'use_tmux': Server_API_Tmux,
        'use_screen': Server_API_Screen
    }

    def __init__(self):
        # Specific API for server interaction depending on server type (vanilla, PaperMC, etc) .
        self.bot = None
        self.last_command_channel_id = None
        self.server_api = None
        self.subprocess_servers = {}
        self.discord_channel = None
        self.server_active = False
        config.update_from_file()  # Reads from json config file if exists.
        self.select_server(config.get_config('selected_server'))
        #self.discord_channel = self.update_discord_chennel(bot)

    # ===== Discord
    def update_bot_object(self, bot: Bot) -> bool:
        """
        Update's Discord bot object in Backend, also tries updating discord_channel.

        Args:
            bot: Discord bot object.

        Returns:
            bool: If successful.
        """

        if isinstance(bot, Bot):
            self.bot = bot
            self.server_api.bot = self.bot
            self.set_discord_channel()
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

    async def send_discord_message(self, msg: str) -> bool:
        """

        Args:
            msg:

        Returns:

        """

        if self.discord_channel is None:
            return False

        await self.discord_channel.send(msg)
        return True

    # ===== Server API
    def select_server(self, server_name: str) -> bool:
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
        if config.get_config('use_subprocess'):
            server_name = config.server_configs['name']
            # Checks if a subprocess API instance for selected server already exists.
            if config.server_configs['name'] in self.subprocess_servers:
                return self.subprocess_servers[server_name]
            else:
                # Create new subprocess API
                new_subprocess_server = Server_API_Subprocess()
                self.subprocess_servers[server_name] = new_subprocess_server
                return True

        for config_name, api in self.server_api_types.items():
            # Checks if corresponding config is enabled to use API, e.g. use_rcon, use_tmux, use_screen, etc...
            if config.get_config(config_name):
                self.server_api = api()  # Set server_api to correct API (Server_API_Tmux, Server_API_Rcon, etc).
                break

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


        # If these configs are set to False, the bot will send the server commands even if status of server status is unknown.
        # If either one is, the bot will only send the command if server console is reachable or successful ping.
        if config.get_config('check_before_command') or config.get_config('ping_before_command'):
            if not await self.console_reachable():
                return False

        if self.server_api.send_command(command):
            self.server_api.last_command_sent = command
            return True

        return False

    # Check if server console is reachable.
    async def console_reachable(self, discord_msg: bool = False) -> Union[bool, None]:
        """
        Check if server console is reachable by sending a unique number to be checked in logs.

        Returns:
            bool, None: Console reachable, or None if unable to get status.
        """

        if await self.server_api.server_console_reachable():
            return True

        if discord_msg:
            await self.send_discord_message("**Server Unreachable**")

        return False

    async def get_command_output(self, keywords: str = None, extra_lines: int = 0) -> Union[str, bool]:
        """

        Returns:

        """

        return await self.server_api.get_command_output(keywords, extra_lines)

    # ===== Start/Stop
    def server_start(self) -> bool:
        """
        Start Minecraft server depending on whether you're using Tmux subprocess method.
        Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

        Returns:
            bool: If successful server launch.
        """

        return self.server_api.server_start()

    # ===== Server status
    # Checks if server is reachable. By sending a command or using ping, depending on configs.
    async def server_status(self, force_check: bool = False) -> bool:
        """
        Returns boolean if server is active.
        Depending on configs, priority: ping_server(), server_console_reachable(), _get_status()

        Returns:
            bool: If server is active (not always same as MC console is reachable).
        """

        # Prioritizes using ping instead of sending command to console.
        if config.get_config('ping_before_command'):
            return self.server_ping()
        # Can force check even if configs disable it.
        elif config.get_config('check_before_command') or force_check:
            return await self.server_api.server_console_reachable()
        return self.server_ping()

    def server_ping(self) -> bool:
        """
        Uses ping command to check if server reachable.

        Returns:
            bool: If ping was successful.
        """

        if address := config.get_config('server_address'):
            return utils.ping_address(address)

        return False

    # Query ping server. Must have 'enable-query=true' in server.properties.
    def server_ping_query(self) -> bool:
        """
        Gets server information using mctools.PINGClient()

        Returns:
            dict: Dictionary containing 'version', and 'description' (motd).
        """


        if not config.get_config('server_address'):
            return False

        try:
            ping = mctools.PINGClient(config.get_config('server_address'), config.get_config('server_port'))
            stats = ping.get_stats()
            ping.stop()
        except ConnectionRefusedError:
            return False
        else:
            return stats

    # ===== Get data
    async def get_motd(self):
        """
        Gets current message of the day from server, either by reading from server.properties file or using PINGClient.

        Returns:
            str: Server motd.
        """

        # Get data from server properties file if able, else use relevant backend.send_command to get it.
        if data := self.get_property('motd'):
            return data
        else:
            pass

    async def get_players(self):
        """Extracts wanted data from output of 'list' command."""

        return await utils.parse_players_output()

    async def get_coords(self, player=''):
        """Gets player's location coordinates."""

        if not backend.send_command(f"data get entity {player} Pos"):
            return False
            #log_data = self.read_server_log('entity data', stopgap_str=response[1])
        # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
        # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
        if log_data := self.get_command_output():
            location = log_data.split('[')[-1][:-3].replace('d', '')
            return location

    def get_server_version(self) -> Union[str, bool]:
        """
        Gets server version number.

        Returns:
            str: Server version.
        """

        # Manual override of server version.
        version = 'N/A'
        if data := config.get_config('server_version'):
            version = data
        elif config.get_config('server_files_access'):
            # Tries to find version info from latest.log.
            if data := self.read_server_log('server version'):
                version = data[0].split('version')[-1].strip()
            # Tries to find info in server.properties next.
            elif data := self.get_property('version'):
                version = data
        #if not version:
            # Get version info from server console.
            #if self.send_command('version'):
                #version = self.server_api.

        return version

    # ===== File reading and writing
    def read_server_log(self, *args, **kwargs):
        return self.server_api.read_server_log(*args, **kwargs)

    def update_property(self, property_name=None, value='', file_path=None):
        """
        Edits server.properties file if received target_property and value. Edits inplace with fileinput
        If receive no value, will return current set value if property exists.

        Args:
            property_name str(None): Find Minecraft server property.
            value str(''): If received argument, will change value.
            file_path str(server.properties): File to edit. Must be in .properties file format. Default is server.properties file under /server folder containing server.jar.

        Returns:
            str: If target_property was not found.
            tuple: First item is line from file that matched target_property. Second item is just the current value.
        """

        if not config.get_config('server_files_access'):
            return False

        # TODO add property file config
        if not file_path:
            file_path = f"{config.get_config('server_path')}/server.properties"

        if not os.path.isfile(file_path):
            return False
        return_line = ''

        # print() writes to file while using it in FileInput() with inplace=True
        # fileinput doc: https://docs.python.org/3/library/fileinput.html
        with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
            for line in file:
                split_line = line.split('=', 1)

                # If found match, and user passed in new value to update it.
                if property_name in split_line[0] and len(split_line) > 1:
                    if value:
                        split_line[1] = value  # edits value section of line
                        new_line = return_line = '='.join(split_line)
                        print(new_line, end='\n')  # Writes new line to file
                    # If user did not pass a new value to update property, just return the line from file.
                    else:
                        return_line = '='.join(split_line)
                        print(line, end='')
                else: print(line, end='')

        # Returns value, and complete line
        if return_line:
            return return_line, return_line.split('=')[1].strip()
        else:
            return False

    def get_property(self, property_name):
        """
        Get a property from server properties file.

        Args:
            property_name str: Property name to get.

        Returns:
            str: Value found.
            bool: If value not found or if not able to access file.
        """

        if config.get_config('server_files_access'):
            if data := self.update_property(property_name):
                return data[1]

        return False

    # ===== Adding/Deleting servers
    def server_new(self, server_name: str) -> Union[Dict, bool]:
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
        if not config.new_server_configs(server_name):
            lprint(f"ERROR: Issue creating new configs for: {server_name}")
            return False

        # Create new folder for server.
        new_folder = join(config.get_config('servers_path'), server_name.strip())
        if not file_utils.new_dir(new_folder):
            return False

        return config.new_server_configs(server_name)

    def server_delete(self, server_name: str) -> Union[Dict, bool]:
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
        config.update_all_server_configs()
        return server_data

    def server_copy(self, server_name: str, new_server_name: str) -> Union[Dict, bool]:
        """

        Args:
            server_name:
            new_server_name:

        Returns:

        """

        if not self.server_new(new_server_name):
            return False

        if server_data := self.server_delete(server_name):
            if file_utils.copy_dir(config.servers[server_name]['server_path'], server_data['server_path']) is False:
                return False
            else:
                return server_data

    # ===== Backup/Restore
    def new_backup(self, new_name, src, dst):
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.
            src str: Folder to backup, whether it's a world folder or a entire server folder.
            dst str: Destination for backup.
        """

        if not file_utils.new_dir(dst):
            return False
        # TODO add multiple world folders backup
        # folder name: version tag if known, date, optional name

        version = self.get_server_version()
        version_text = f"{'v(' + version + ') ' if 'N/A' not in version else ''}"
        new_name = f"({utils.get_datetime()}) {version_text}{new_name}"
        new_backup_path = join(dst, new_name.strip())
        file_utils.copy_dir(src, new_backup_path)
        return new_backup_path

    def restore_backup(self, src, dst):
        """
        Restores world or server backup. Overwrites existing files.

        Args:
            src str: Backed up folder to copy to current server.
            dst str: Location to copy backup to.
        """

        if file_utils.delete_dir(dst):
            file_utils.copy_dir(src, dst)

    def delete_backup(self, path):
        """

        Args:
            path:

        Returns:

        """
        file_utils.delete_dir(path)


backend = Backend()
