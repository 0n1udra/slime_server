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
import re
import asyncio
import requests
import fileinput
from os.path import join
from collections import deque
from typing import Union, Dict

from discord.ext.commands import Bot
import mctools
from file_read_backwards import FileReadBackwards

from bot_files.server_api import Server_API, Server_API_Screen, Server_API_Subprocess, Server_API_Rcon, Server_API_Tmux
from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils, file_utils


# Used for removing ANSI escape characters
ctx = 'backend_functions.py'


class Backend:
    # The order of this dictionary determines the priority of which API to use if multiple are enabled in configs.
    server_api_types = {
        'use_rcon': Server_API_Rcon,
        'use_tmux': Server_API_Tmux,
        'use_screen': Server_API_Screen
    }

    def __init__(self):
        # Specific API for server interaction depending on server type (vanilla, PaperMC, etc) .
        self.bot = None
        self.server_api = Server_API()
        self.subprocess_servers = {}
        self.discord_channel = None
        self.server_active = False
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

        if bot:
            self.bot = bot
            self.update_discord_channel()
            return True
        return False

    def update_discord_channel(self) -> bool:
        """
        Updates discord_channel with Discord channel object wtih channel_id config, so you can use send_channel_msg func.

        Args:
            bot: Needs discord.ext.commands.bot object to send message to find channel by ID.

        Returns:
            bool: Successfully found Discord chanel by set channel_id config.
        """

        if channel_id := config.get_config('channel_id'):
            try: channel_id = int(channel_id)  # Basic check if valid ID.
            except:
                lprint("ERROR: Invalid Channel ID")
                return False
            else:
                self.discord_channel = self.bot.get_channel(channel_id)
                return True

    async def send_channel_msg(self, msg: str) -> bool:
        """
        Send message to set channel from channel_id config.

        Args:
            msg str: Message to send to channel.

        Returns:
            bool:
        """

        # TODO: Fix return actually successful send
        if self.discord_channel:
            await self.discord_channel.send(msg)
            return True
        else: return False

    # ===== Server API
    def select_server(self, server_name: str) -> bool:
        """
        Updates relevant server command functions and configs.

        Args:
            server_name: Server to select.

        Returns:
            bool: Successful switch.
        """

        if config.switch_server_configs(server_name) is True:
            if self._change_server_api() is True:
                return True
        return False

    def _update_subprocess_api(self) -> Server_API_Subprocess:
        """
        Using subprocess needs special handling to preserve possible running Minecraft subprocesses process.

        Returns:
            Server_API_Subprocess: A server subprocess API object.
        """

        server_name = config.selected_server['name']

        # Checks if a subprocess API instance for selected server already exists.
        if config.selected_server['name'] in self.subprocess_servers:
            return self.subprocess_servers[config.selected_server['name']]
        else:
            # Create new subprocess API
            new_subprocess_server = Server_API_Subprocess()
            self.subprocess_servers[server_name] = new_subprocess_server
            return new_subprocess_server

    def _change_server_api(self) -> bool:
        """
        Updates the server_api object depending on server configs.

        Returns:
            bool: If updated successfully.

        """

        # In cases of wanting to use subprocess to run Minecraft server and have the ability to switch servers to control.
        # This needs its own object so you can switch between them without killing the Minecraft server subprocess.
        if config.get_config('use_subprocess') is True:
            self.server_api = self._update_subprocess_api()
        for config_name, api in self.server_api_types.items():
            # Checks if corresponding config is enabled to use API, e.g. use_rcon, use_tmux, use_screen, etc...
            if config.get_config(config_name) is True:
                self.server_api = api()
                return True
        else: return True

    # Need?
    def get_selected_server(self):
        """
        Returns configs dictionary of currently selected server.

        Returns:
            dict: Configs dict of selected server.
        """
        return config.server_configs

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

        if self.server_api.send_command(command) is True:
            await asyncio.sleep(config.get_config('command_buffer_time'))
            return True
        return False

    # Check if server console is reachable.
    async def console_reachable(self) -> bool:
        """
        Check if server console is reachable by sending a unique number to be checked in logs.

        Returns:
            bool: Console reachable.
        """

        return self.server_api.server_console_reachable()

    def get_command_output(self) -> Union[str, bool]:
        """

        Returns:

        """

        return self.server_api.get_command_output()

    # ===== Server Functions
    async def get_status(self, force_check: bool = False) -> bool:
        """
        Returns boolean if server is active.
        Depending on configs, prioritizes ping_server(), server_console_reachable(), _get_status()

        Returns:
            bool: If server is active (not same as MC console is reachable).
        """

        if config.get_config('ping_before_command') is True:
            return self.server_ping()
        # Can force check even if configs disable it.
        elif config.get_config('check_before_command') is True or force_check is True:
            return await self.server_api.server_console_reachable()

        return False
    
    def server_start(self) -> bool:
        """
        Start Minecraft server depending on whether you're using Tmux subprocess method.
        Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

        Returns:
            bool: If successful server launch.
        """

        return self.server_api.start_server()

    def server_ping(self) -> bool:
        """
        Uses ping command to check if server reachable.

        Returns:
            bool: If ping was successful.
        """

        if address := config.get_config('server_address'):
            return utils.ping_address(address)
        return False

    def server_ping_query(self) -> bool:
        """
        Gets server information using mctools.PINGClient()

        Returns:
            dict: Dictionary containing 'version', and 'description' (motd).
        """


        if not config.get_config('server_address'): return False

        try:
            ping = mctools.PINGClient(config.get_config('server_address'), config.get_config('server_port'))
            stats = ping.get_stats()
            ping.stop()
        except ConnectionRefusedError:
            return False
        else: return stats

    async def server_status(self, discord_msg=False):
        """
        Gets server active status, by sending command to server and checking server log.

        Returns:
            bool: returns True if server is online.
        """

        # Uses ping to check if server is online.
        if config.get_config('ping_before_command') is True:
            response = self.ping_server()
        else:
            # send_command() will send random number, server is online if match is found in log.
            if response := self.server_console_reachable() is not None:
                response = response
            else: response = self.ping_server()  # Fallback on using ping for server status.

        #self.server_active = response
        return response

    async def get_players(self):
        """Extracts wanted data from output of 'list' command."""

        response = await send_command("list", discord_msg=False)
        if not response: return False

        # Gets data from RCON response or reads server log for line containing player names.
        if config.get_config('server_use_rcon') is True:
            log_data = response[0]

        else:
            await asyncio.sleep(1)
            log_data = server_log('players online')

        if data := utils.parse_get_player_info(log_data):
            return data
        return False

    async def get_coords(self, player=''):
        """Gets player's location coordinates."""

        if response := await send_command(f"data get entity {player} Pos", skip_check=True):
            log_data = server_log('entity data', stopgap_str=response[1])
            # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
            # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
            if log_data:
                location = log_data.split('[')[-1][:-3].replace('d', '')
                return location



    # File reading and writing
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

        if config.get_config('server_files_access') is False: return False
        # TODO add property file config
        if not file_path: file_path = f"{config.get_config('server_path')}/server.properties"
        if not os.path.isfile(file_path): return False
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
        else: return "Match not found.", 'Match not found.'

    def get_property(self, property_name):
        """
        Get a property from server properties file.

        Args:
            property_name str: Property name to get.

        Returns:
            str: Value found.
            bool: If value not found or if not able to access file.
        """

        if config.get_config('server_files_access') is True:
            if data := self.update_property(property_name):
                return data[1]
        return False

    def get_motd(self):
        """
        Gets current message of the day from server, either by reading from server.properties file or using PINGClient.

        Returns:
            str: Server motd.
        """

        # Get data from server properties file if able, else use relevant send_command to get it.
        if data := self.get_property('motd'):
            return data
        else:
            pass

    # ===== Backups
    def new_server(self, server_name: str) -> Union[Dict, bool]:
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            server_name str: Name of new server.

        Returns:
            dict, bool: Dictionary of new server configs or False if failed.
        """

        new_folder = join(config.get_config('servers_path'), server_name.strip())
        try: os.mkdir(new_folder)
        except:
            lprint("ERROR: Problem creating new server folder")
            return False
        else: return config.update_server_configs(server_name)


    def new_backup(self, new_name, src, dst):
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.
            src str: Folder to backup, whether it's a world folder or a entire server folder.
            dst str: Destination for backup.
        """

        if not isdir(dst): os.makedirs(dst)
        # TODO add multiple world folders backup
        # folder name: version tag if known, date, optional name
        version = f"{'v(' + server_version() + ') ' if 'N/A' not in server_version() else ''}"
        new_name = f"({extra.get_datetime()}) {version}{new_name}"
        new_backup_path = join(dst, new_name.strip())
        shutil.copytree(src, new_backup_path)
        return new_backup_path

    def restore_backup(self, src, dst):
        """
        Restores world or server backup. Overwrites existing files.

        Args:
            src str: Backed up folder to copy to current server.
            dst str: Location to copy backup to.
        """

        shutil.rmtree(dst)
        shutil.copytree(src, dst)


backend = Backend()
# ========== Server Commands: start, send command, read log, etc

