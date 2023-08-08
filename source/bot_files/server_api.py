"""
Handles how to interact with the Minecraft server based on the configs.
Inside Backend object there is the _change_server_api() function,
  which decides which Server_API_X class to set as self.server_api in the 'Backend' object.
For example, if the 'use_tmux' config is True, _change_server_api() will use a new instance of 'Server_API_Tmux'.
I'm using Python class inheritance, it works by override certain functions in base 'Server_API' class.
Each Server_API_X class should have its own send_command() with its own way to interact with the server.
For example, in Server_API_Tmux it uses os.system() to send commands to a tmux pane containing the server console,
  and in Server_API_Rcon, it uses the mctools module to send the command using RCON.
The functions starting with '_' are expected to be overridden in the inheritance of Server_API.

Following functions must be async:
    send_command()
    get_command_output()
    server_start()
"""

import os
import json
import asyncio
import requests
import subprocess
from collections import deque
from typing import Union, Any, Callable, Tuple, List

import mctools
from bs4 import BeautifulSoup
from file_read_backwards import FileReadBackwards

from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils, file_utils


class Server_Update:
    """
    This class handles finding the latest direct download link for different server types.
    For each server type (vanilla, PaperMC, Bukkit, etc) you need to have a get_X_url() function.
    These URL getter functions need to find a way to get the latest server (usually .jar) file direct download link.
    Which getter function to use is based on if keywords were found in selected server's name and description.
    Structure of url_builder_functions dict:
        Dict keys is a list of keywords to find in name and description of currently selected server.
        Dict values is a callable function used to build direct download URL for latest server.
    """

    def __init__(self):
        self.url_builder_functions = {
            'vanilla': [self.get_vanilla_url, ['vanillla']],
            'paper': [self.get_papermc_url, ['paper']],
            'bukkit': [self.get_bukkit_url, ['bukkit']],
        }

    def _check_latest_version(self):
        """
        Gets latest Minecraft server version number from official website using bs4.

        Returns:
            str: Latest version number.
        """

        soup = BeautifulSoup(requests.get(config.get_config('new_server_address')).text, 'html.parser')
        for i in soup.findAll('a'):
            if i.string and 'minecraft_server' in i.string:
                return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.

    def server_update(self) -> Union[Tuple[str], bool]:
        """

        Returns:

        """

        # Picks what url builder function to use based on name and description of selected server.
        url_getter = self.get_url_func()
        if not url_getter:
            return False

        version_info, download_url = url_getter()
        download_data = requests.get(download_url).content

        try:  # Sets eula.txt file.
            with open(config.get_config('server_path') + '/eula.txt', 'w+') as f: f.write('eula=true')
        except IOError:
            lprint(f"ERROR: Updating eula.txt file: {config.get_config('server_path')}")

        try:  # Saves file as server.jar.
            with open(config.get_config('server_path') + '/server.jar', 'wb+') as f: f.write(download_data)
        except IOError:
            lprint(f"ERROR: Saving new jar file: {config.get_config('server_path')}")
        else:
            return download_url, version_info

        return False

    def get_url_func(self) -> Union[Callable, None]:
        """
        Picks what get_x_url() function to use based on name/description of selected server.

        Returns:
            Callable, None: Returns callable function or None.
        """

        # Checks if server name and description contains keyword to determine what url builder func to use.
        for k, v in self.url_builder_functions.items():
            if any(i in config.server_configs['server_name'] for i in v[1]):
                return v[0]
            elif any(i in config.server_configs['server_description'] for i in v[1]):
                return v[0]
        return None

    def get_vanilla_url(self) -> Tuple[str, str]:
        """
        Get direct download URL for vanilla Minecraft server.

        Returns:
            Tuple[str]: Tuple of download URL and version info.
        """

        download_url = version_info = ''
        def get_json_data(url): return json.loads(requests.get(url).text)
        # Finds latest release from manifest and gets required data.
        manifest = get_json_data('https://launchermeta.mojang.com/mc/game/version_manifest.json')
        for i in manifest['versions']:
            if i['type'] == 'release':
                version_info = f"{i['id']} ({i['time']})"
                download_url = get_json_data(i['url'])['downloads']['server']['url']
                break  # Breaks loop on firest release found (should be latest).
        return download_url, version_info

    def get_papermc_url(self) -> Tuple[str, str]:
        """
        Get direct download URL for latest PaperMC server.

        Returns:
            Tuple[str]: Tuple of download URL and version info.
        """

        base_url = 'https://papermc.io/api/v2/projects/paper'
        # Extracts required data for download URL. PaperMC API: https://papermc.io/api/docs/swagger-ui/index.html?configUrl=/api/openapi/swagger-config
        def get_data(find, url=''): return json.loads(requests.get(f'{base_url}{url}').text)[find]
        latest_version = get_data('versions')[-1]  # Gets latest Minecraft version (e.g. 1.18.2).
        latest_build = get_data('builds', f'/versions/{latest_version}')[-1]  # Get PaperMC Paper latest build (277).
        # Get file name to download (paper-1.18.2-277.jar).
        latest_jar = version_info = get_data('downloads', f'/versions/{latest_version}/builds/{latest_build}')['application']['name']
        # Full download URL: https://papermc.io/api/v2/projects/paper/versions/1.18.2/builds/277/downloads/paper-1.18.2-277.jar
        jar_download_url = f'{base_url}/versions/{latest_version}/builds/{latest_build}/downloads/{latest_jar}'
        return jar_download_url, version_info

    def get_bukkit_url(self): pass


class Server_API(Server_Update):
    """
    Depending on configs, using class inheritance relevant functions will be updated.
    server_console_reachable()
    send_command()

    """

    def __init__(self):
        super().__init__()

        self.bot = None
        self.last_check_number = ''
        self.last_command_sent = ''
        self.last_command_output = ''

        # Set server launch path depending on config.
        self.launch_path = config.get_config('server_path')
        if custom_path := config.get_config('server_launch_path'):
            self.launch_path = custom_path

        self.launch_command = config.get_config('server_launch_command')
        if config.get_config('windows_compatibility'):
            self.launch_command = f"{config.get_config('windows_cmdline_start')} {self.launch_command}"

    # This will be updated with correct code to send command to server console based on configs.
    async def send_command(self, command: str) -> bool:
        """
        Send command to Minecraft server.

        Args:
            command str: Command to send to server.

        Returns:
            bool: If successfully sent command, not the same as if command accepted by server.
        """

        return False

    # Check if server console is reachable.
    async def server_console_reachable(self) -> bool:
        """
        Check if server console is reachable by sending a unique number to be checked in logs.

        Returns:
            bool: Console reachable.
        """

        if config.get_config('server_files_access'):
            check_command, unique_number = utils.get_check_command()  # Custom command to send with unique number.
            if await self.send_command(check_command):
                if await self.get_command_output(unique_number, check_number=unique_number) is not False:  # Check logs for unique number.
                    self.last_check_number = unique_number
                    return True

        return False

    # Get output from the last issued command.
    async def get_command_output(self, keyword: str = None, extra_lines: int = 0, check_number: str = None, all_lines=False) -> Union[str, bool]:
        """
        Gets response from last command.

        Returns:
            str: Response from last command issued.
        """

        # Can only get command output from server log if there's a check number (e.g. xp 0.45151...).
        # If there's no unique number to use as a stopgap the bot might return the output from a prior command.
        if not check_number and not self.last_check_number:
            return False
        else: check_number = self.last_check_number

        await asyncio.sleep(config.get_config('command_buffer_time'))
        if data := await self.read_server_log(search=keyword, extra_lines=extra_lines, find_all=all_lines, stopgap_str=check_number):
            return data

        return False

    # ===== Server Files
    async def read_server_log(self, search: str = None, lines: int = 15, extra_lines: int = 0,
                              find_all: bool = False, stopgap_str: str = None,
                              top_down_mode: bool = False) -> Union[List, bool]:
        """
        Read the latest.log file under server/logs folder. Can also find a match.

        Args:
            search (str or list, optional): Check for a matching string or a list of matching strings.
                                            If None, it will return all log data without matching.
            file_path (str, optional): File to read. Defaults to the server's latest.log.
            lines (int, optional): Number of most recent lines to return.
            extra_lines int(0): For cases where command output is multi-lined.
            find_all bool(False): Find all occurrences in latest.log.
            stopgap_str (str, optional): Stops the search when this string is found in the log line.
            top_down_mode (bool, optional): If True, search from the top of the log file.
                                            If False (default), search from the bottom of the log file.

        Returns:
            list: Matched lines.
        """

        if not isinstance(search, list): search = [search]

        file_path = config.get_config('server_log_filepath')  # server.properties file as default file.
        if not file_utils.test_file(file_path):
            return False

        # Create a deque, which will efficiently store the most recent matched log lines.
        matched_lines = []

        # Changes function to read file if reading bottom up or top down.
        read_log_lines = file_utils.read_file_generator if top_down_mode else file_utils.read_file_reverse_generator
        _extra_lines = deque(maxlen=extra_lines + 1)
        for line in read_log_lines(file_path):
            # If None search, will return all lines. Else, checks if line matches any of search keywords.
            if search[0] is None or any([str(s).lower() in line.lower() for s in search]):
                matched_lines.append(line)
                if not find_all:
                    break  # find_all = True means find all occurrences in file.

            # Needed for some multi-line outputs for some commands (e.g. list command in 1.12)
            if extra_lines: _extra_lines.append(line)

            # Stops if found stopgap_str in line or at the limit user specified.
            if (stopgap_str and stopgap_str in line) or len(matched_lines) >= lines:
                break

        return list(reversed(matched_lines + list(_extra_lines)))

    async def server_start(self) -> bool:
        """
        Start server.

        Returns:
            bool: Sent startup command (Not same as successful startup).
        """

        return False

    async def server_stop(self) -> bool:
        """
        Stop server.

        Returns:
            bool: Sent stop command (Not same as successful stopped).
        """

        return await self.send_command('stop')


class Server_API_Tmux(Server_API):
    def __init__(self):
        super().__init__()

    async def send_command(self, command: str) -> bool:
        """
        Sends command to Minecraft server console in Tmux session.

        Args:
            command: Command to send.

        Returns:
            bool: If os.system() command was successful (not if MC command was successful).
        """

        if os.system(f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_minecraft_pane')} '{command}' ENTER"):
            return False

        return True

    async def server_start(self) -> bool:
        """
        Start server in specified Tmux pane.

        Returns:
            bool: If os.system() was successful.
        """

        # If failed to change current working directory.
        if os.system(f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_minecraft_pane')} 'cd {self.launch_path}' ENTER"):
            lprint("ERROR: Could not change directory to server launch path.")
            return False

        # Starts server in tmux pane.
        if os.system(f"tmux send-keys -t {config.get_config('tmux_session_name')}:{config.get_config('tmux_minecraft_pane')} '{self.launch_command}' ENTER"):
            lprint("ERROR: Problem with server launch command.")
            return False

        return True


class Server_API_Screen(Server_API):
    def __init__(self):
        super().__init__()

    async def send_command(self, command: str) -> bool:
        """
        Sends command to Minecraft server console in Screen session.

        Args:
            command: Command to send.

        Returns:
            bool: If os.system() command was successful (not if MC command was successful).
        """

        if os.system(f"screen -S {config.get_config('screen_session_name')} -X stuff '{command}^M'"):
            return False

        return True

    async def server_start(self) -> bool:
        """
        Start server in specified screen session.

        Returns:
            bool: If os.system() was successful.
        """

        os.chdir(self.launch_path)
        if os.system(f"screen -dmS '{config.get_config('screen_session_name')}' {self.launch_command}"):
            lprint(f"ERROR: Could not start server with screen: {self.launch_command}")
            return False

        return True


class Server_API_Rcon(Server_API):
    def __init__(self):
        super().__init__()

    async def send_command(self, command: str) -> Union[str, bool]:
        """
        Send command to server with RCON.

        Args:
            command str: Minecraft server command.

        Returns:
            str, bool: Output from RCON or False if error.
        """

        # TODO possibly add persistent connection
        server_rcon_client = mctools.RCONClient(config.get_config('server_address'), port=config.get_config('rcon_port'))
        try:
            server_rcon_client.login(config.get_config('rcon_pass'))  # Connect to server
        except ConnectionError:
            lprint(f"Error Connecting to RCON: {config.get_config('server_ip')} : {config.get_config('rcon_port')}")
            return False
        else:
            self.last_command_output = server_rcon_client.command(command)  # Send command and get output.
            server_rcon_client.stop()  # Disconnect.
            return self.last_command_output

    async def server_console_reachable(self) -> bool:
        """
        Check if server console is reachable by sending a unique number.

        Returns:
            bool: Console reachable.
        """

        check_command, unique_number = utils.get_check_command()
        if response := await self.send_command(check_command):
            if unique_number in response:
                return True

        return False


class Server_API_Subprocess(Server_API):
    def __init__(self):
        super().__init__()

        self.server_subprocess = None

    # TODO be able to have multiple subprocess servers running and switch between them
    async def send_command(self, command):
        if not self.server_subprocess:
            return False

        try:
            self.server_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
            self.server_subprocess.stdin.flush()
        except:
            return False
        else:
            self.last_command_output = self.server_subprocess.stdout.readline().decode('utf-8')
            self.server_subprocess.wait()

        return True

    async def server_start(self) -> bool:
        """

        Returns:

        """

        os.chdir(self.launch_path)
        # Runs MC server as subprocess. Note, If this script stops, the server will stop.
        try:
            if config.get_config('windows_compatibility'):
                self.server_subprocess = subprocess.Popen(
                    config.get_config(self.launch_command),
                    shell=True
                )
            else:
                self.server_subprocess = subprocess.Popen(
                    self.launch_command.split(),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
        except: lprint("ERROR: Problem starting server subprocess")

        if isinstance(self.server_subprocess, subprocess.Popen):
            return True

        return False
        # TODO TEST for windows compatibility
