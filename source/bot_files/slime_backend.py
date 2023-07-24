import os
import re
import asyncio
import requests
import fileinput
from os.path import join
from collections import deque

import mctools
from file_read_backwards import FileReadBackwards
from bot_files.slime_config import config
from bot_files.slime_utils import lprint
from bot_files.server_api import Server_Screen_API, Server_Subprocess_API, Server_Rcon_API, Server_Tmux_API
from bot_files.slime_utils import utils, file_utils


# Used for removing ANSI escape characters
ctx = 'backend_functions.py'


class Backend:
    server_api_types = {'use_rcon': Server_Rcon_API, 'use_tmux': Server_Tmux_API, 'use_screen': Server_Screen_API}
    subprocess_servers = {}

    def __init__(self, bot=None):
        self.server_active = False
        self.discord_channel = self.update_discord_chennel(bot)

    def update_discord_channel(self, bot=None):
        """
        Updates discord_channel with Discord channel object wtih channel_id config, so you can use send_channel_msg func.

        Args:
            bot: Needs discord.ext.commands.bot object to send message to find channel by ID.

        Returns:
            bool: Successfully found Discord chanel by set channel_id config.
        """

        if channel_id := config.get('channel_id'):
            try: channel_id = int(channel_id)  # Basic check if valid ID.
            except:
                lprint(ctx, "ERROR: Invalid Channel ID")
                return False
            else:
                self.discord_channel = bot.get_channel(channel_id)
                return True

    async def send_channel_msg(self, msg):
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

    def select_server(self, server_name):
        """
        Updates relevant server command functions and configs.

        Args:
            server_name: Server to select.

        Returns:
            bool: Successful switch.
        """

        pass

    def _update_subprocess_api(self):
        """
        Using subprocess needs special handling to preserve possible running Minecraft subprocesses process.

        Returns:
            dict: Dictionary containing configs and server subprocess object.
        """

        pass

    def _change_server_api(self):
        """
        Updates the server_api object depending on server configs.

        Returns:
            bool: If updated successfully.

        """

        # In cases of wanting to use subprocess to run Minecraft server and have the ability to switch servers to control.
        # This needs its own object so you can switch between them without killing the Minecraft server subprocess.
        if config.get('use_subprocess') is True:
            self.server_api = self._update_subprocess_api()
        for config_name, api in self.server_api_types.items():
            if config.get(config_name) is True:
                self.server_api = api()
                return True
        else: return True

    def get_selected_server(self):
        """
        Returns configs dictionary of currently selected server.

        Returns:
            dict: Configs dict of selected server.
        """
        return config.server_configs


    def read_server_log(self, search=None, file_path=None, lines=15, find_all=False, stopgap_str=None, top_down_mode=False):
        """
        Read the latest.log file under server/logs folder. Can also find a match.

        Args:
            search (str or list, optional): Check for a matching string or a list of matching strings.
                                            If None, it will return all log data without matching.
            file_path (str, optional): File to read. Defaults to the server's latest.log.
            lines (int, optional): Number of most recent lines to return.
            match_mode (str, optional): Matching mode. Options: 'any' (default), 'all', 'none'.
            stopgap_str (str, optional): Stops the search when this string is found in the log line.
            top_down_mode (bool, optional): If True, search from the top of the log file.
                                            If False (default), search from the bottom of the log file.

        Returns:
            str: Matched lines in reverse order, joined by '\n'.
        """
        # Convert the search strings to lowercase for case-insensitive matching.
        if type(search) is str:
            search = [search.lower()]
        elif type(search) is list:
            search = [s.lower() for s in search]
        else: search = None

        file_path = file_path or config.get('server_log_filepath')  # server.properties file as default file.
        if not file_path or not os.path.exists(file_path): return False  # If file not exist.

        # Create a deque, which will efficiently store the most recent matched log lines.
        matched_lines = deque(maxlen=lines) if top_down_mode else []

        # Changes function to read file if reading bottom up or top down.
        read_log_lines = file_utils.read_file_bottom_up if not top_down_mode  else file_utils.read_file
        with read_log_lines(file_path, top_down_mode) as log_lines:
            for line in log_lines:
                # Check if each element in 'search' is found in 'line_lower'.
                found_matches = [s in line.lower() for s in search]
                # Determine if the line matches the specified criteria (search and match_mode).
                # The conditions use 'found_matches', which is a list of booleans indicating the match status.
                if search is None or ((not find_all and any(found_matches)) or (find_all and all(found_matches))):
                    # Append the matched line to the deque or list depending on the search mode.
                    matched_lines.append(line)

                    # Stops if found stopgap_str in line or at the limit user specified.
                    if (stopgap_str and stopgap_str in line) or len(matched_lines) >= lines: break

        return '\n'.join(matched_lines)

    # File reading and writing
    def _read_server_log(self, match=None, match_list=[], file_path=None, lines=15, normal_read=False, log_mode=False, filter_mode=False, stopgap_str=None, return_reversed=False):
        """
        Read latest.log file under server/logs folder. Can also find match.
        What a fat ugly function you are :(

        Args:
            match str: Check for matching string.
            file_path str(None): File to read. Defaults to server's latest.log
            lines int(15): Number of most recent lines to return.
            log_mode bool(False): Return x lines from log file, skips matching.
            normal_read bool(False): Reads file top down, defaults to bottom up using file-read-backwards module.
            filter_mode bool(False): Don't stop at first match.
            return_reversed bool(False): Returns so ordering is newest at bottom going up for older.

        Returns:
            log_data (str): Returns found match log line or multiple lines from log.
        """

        global slime_vars

        # Parameter setups.
        if match is None: match = 'placeholder_match'
        match = match.lower()
        if stopgap_str is None: stopgap_str = 'placeholder_stopgap'
        # Defaults file to server log.
        if file_path is None: file_path = config.get('server_log_filepath')
        if not os.path.isfile(file_path): return False

        log_data = ''  # TODO: Possibly change return data to list for each newline

        # Gets file line number
        line_count = sum(1 for line in open(file_path))

        if normal_read:
            with open(file_path, 'r') as file:
                for line in file:
                    if match in line: return line

        else:  # Read log file bottom up, latest log outputs first.
            with FileReadBackwards(file_path) as file:
                i = total = 0
                # Stops loop at user set limit, if file has no more lines, or at hard limit (don't let user ask for 999 lines of log).
                while i < lines and total < line_count and total <= config.get('log_lines_limit'):
                    total += 1
                    line = file.readline()
                    if not line.strip(): continue  # Skip blank/newlines.
                    elif log_mode:
                        log_data += line
                        i += 1
                    elif match in line.lower() or any(i in line for i in match_list):
                        log_data += line
                        i += 1
                        if not filter_mode: break  # If filter_mode is not True, loop will stop at first match.
                    if stopgap_str.lower() in line.lower(): break  # Stops loop if using stopgap_str variable. e.g. Using with filter_mode.

        if log_data:
            if return_reversed is True:
                log_data = '\n'.join(list(reversed(log_data.split('\n'))))[1:]  # Reversed line ordering, so most recent lines are at bottom.
            return log_data

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

        if config.get('server_files_access') is False: return False
        # TODO add property file config
        if not file_path: file_path = f"{config.get('server_path')}/server.properties"
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

        if config.get('server_files_access') is True:
            if data := self.update_property(property_name):
                return data[1]
        return False


    def _get_motd(self): pass

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
            if data := self._get_motd():
                return data
            else: return 'N/A'


    def server_start():
        """
        Start Minecraft server depending on whether you're using Tmux subprocess method.

        Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

        Returns:
            bool: If successful boot.
        """

        global mc_subprocess

        if config.get('server_use_screen') is True:
            os.chdir(config.get('server_path'))
            if not os.system(f"screen -dmS '{config.get('screen_session_name')}' {config.get('server_launch_command')}"):
                return True
            else: return False

        elif config.get('server_use_subprocess') is True:
            # Runs MC server as subprocess. Note, If this script stops, the server will stop.
            try:
                mc_subprocess = subprocess.Popen(config.get('server_launch_command').split(), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            except: lprint(ctx, "Error server starting subprocess")

            if type(mc_subprocess) == subprocess.Popen: return True

        # Start java server using subprocess and cmd's Launch Command.
        elif config.get('windows_compatibility') is True:
            os.chdir(config.get('server_path'))
            subprocess.Popen(config.get('windows_cmdline_start') + config.get('server_launch_command'), shell=True)

        elif config.get('use_tmux') is True:
            os.system(f"tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} 'cd {config.get('server_path')}' ENTER")

            # Starts server in tmux pane.
            if not os.system(f'tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} "{config.get('server_launch_command')}" ENTER'):
                return True
        else: return False



    def server_ping(self):
        """
        Uses ping command to check if server reachable.

        Returns:
            bool: If ping was successful.
        """
        utils.ping_address()

    def server_ping_query(self):
        """
        Gets server information using mctools.PINGClient()

        Returns:
            dict: Dictionary containing 'version', and 'description' (motd).
        """

        global server_active

        if not config.get('server_address'): return False

        try:
            ping = mctools.PINGClient(config.get('server_address'), config.get('server_port'))
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
        if config.get('ping_before_command') is True:
            response = utils.ping_address(config.get('server_address'))
        else:
            # send_command() will send random number, server is online if match is found in log.
            response = await self.send_command(' ', discord_msg=discord_msg, force_check=True, ctx=ctx)

        self.server_active = response
        return response


    async def get_players(self):
        """Extracts wanted data from output of 'list' command."""

        # Converts server version to usable int. Extracts number after initial '1.', e.g. '1.12.2' > 12
        try: version = int(server_version().split('.')[1])
        except: version = 20
        # In version 1.12 and lower, the /list command outputs usernames on a newline from the 'There are x players' line.
        if version <= 12:
            response = await send_command("list", discord_msg=False)
            # Need to use server_log here because I need to get multiple line outputs.
            log_data = server_log(log_mode=True, stopgap_str=response[1])
            # Parses and returns info from log lines.
            output = []
            for i in log_data.split('\n'):
                output.append(i)
                if 'There are' in i: break
            output = output[:2]
            if not output: return False
            # Parses data from log output. Ex: There are 2 of a max of 20 players online: R3diculous, MysticFrogo
            text = output[1].split(':')[-2].strip()
            player_names = output[0].split(':')[-1].split(',')
            return player_names, text
        else:
            response = await send_command("list", discord_msg=False)
            if not response: return False

            # Gets data from RCON response or reads server log for line containing player names.
            if config.get('server_use_rcon') is True: log_data = response[0]

            else:
                await asyncio.sleep(1)
                log_data = server_log('players online')

            if not log_data: return False

            find_ansi = re.compile(r'\x1b[^m]*m')
            # Use regular expression to extract player names
            log_data = log_data.split(':')  # [23:08:55 INFO]: There are 2 of a max of 20 players online: R3diculous, MysticFrogo
            text = log_data[-2]  # There are 2 of a max of 20 players online
            text = find_ansi.sub('', text)  # Remove unwanted escape characters
            player_names = log_data[-1]  # R3diculous, MysticFrogo
            # If there's no players active, player_names will still contain some anso escape characters.
            if len(player_names.strip()) < 5: return None
            else:

                player_names = [f"{i.strip()[:-4]}\n" if config.get('server_use_rcon') else f"{i.strip()}" for i in (log_data[-1]).split(',')]
                # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
                # player_names_discord = [f"`{i.strip()[:-4]}`\n" if server_use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]
                new = []
                for i in player_names:
                    x = find_ansi.sub('', i).strip().replace('[3', '')
                    x = x.split(' ')[-1]
                    x = x.replace('\\x1b', '').strip()
                    new.append(x)
                player_names = new
                return player_names, text

    async def get_coords(self, player=''):
        """Gets player's location coordinates."""

        if response := await send_command(f"data get entity {player} Pos", skip_check=True):
            log_data = server_log('entity data', stopgap_str=response[1])
            # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
            # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
            if log_data:
                location = log_data.split('[')[-1][:-3].replace('d', '')
                return location


    def new_server(self, name):
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.
            src str: Folder to backup, whether it's a world folder or a entire server folder.
            dst str: Destination for backup.
        """

        new_folder = join(config.get('servers_path'), name.strip())
        os.mkdir(new_folder)
        return new_folder

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

