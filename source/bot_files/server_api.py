import os
import json
import asyncio
import requests
from typing import Union, Any, Callable, Tuple, List

import mctools
from bs4 import BeautifulSoup

from slime_utils import utils
from slime_utils import lprint
from slime_config import config

class Server_Files:
    def get_property(self, key: str) -> Any:
        """

        Args:
            key:

        Returns:

        """

        pass

    def set_property(self, key: str, value: Any) -> bool:
        """

        Args:
            key:
            value:

        Returns:

        """

        pass


class Server_Versioning(Server_Files):

    def __init__(self):
        self.url_builder_functions = {
            ['vanilla']: self.get_vanilla_url,
            ['paper']: self.get_papermc_url,
            ['bukkit']: self.get_bukkit_url,
        }
        self.download_link = ''

    def _get_server_version(self) -> str:
        """
        Get Minecraft server version.

        Returns:
            str: Server version.
        """

        return 'N/A'

    def get_server_version(self) -> str:
        """
        Gets server version, either by reading server log or using PINGClient.

        Returns:
            str: Server version.
        """

        # Manual override of server version.
        version = 'N/A'
        if data := config.get('server_version'):
            version = data
        elif config.get('server_files_access') is True:
            if data := self.server_log('server version'):
                version = data.split('version')[1].strip()
            elif data := self.get_property('version'):
                version = data
        else:
            version = self._get_server_version()
        return version

    def check_latest_version(self):
        """
        Gets latest Minecraft server version number from official website using bs4.

        Returns:
            str: Latest version number.
        """

        soup = BeautifulSoup(requests.get(config.get('new_server_address')).text, 'html.parser')
        for i in soup.findAll('a'):
            if i.string and 'minecraft_server' in i.string:
                return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.

    def server_update(self) -> Union[Tuple[str], bool]:
        """

        Returns:

        """

        # Picks what url builder function to use based on name and description of selected server.
        if not self.pick_url_builder(): return False

        version_info, download_url = self.downloader()
        requests.get(download_url).content
        def check(type):

        try:  # Sets eula.txt file.
            with open(config.get('server_path') + '/eula.txt', 'w+') as f: f.write('eula=true')
        except IOError: lprint(f"ERROR: Updating eula.txt file: {config.get('server_path')}")

        try:  # Saves file as server.jar.
            with open(config.get('server_path') + '/server.jar', 'wb+') as f: f.write(new_jar_data)
        except IOError: lprint(f"ERROR: Saving new jar file: {config.get('server_path')}")
        else:
            return download_url, version_info
        return False

    def pick_url_builder(self) -> Union[Callable, None]:
        """
        Picks what get_x_url() function to use based on name/description of selected server.

        Returns:
            Callable, None: Returns callable function or None.
        """

        # Checks if server name and description contains keyword to determine what url builder func to use.
        for name, function in self.url_builder_functions.items():
            if any(i in config.selected_server['name'] for i in name):
                return function
            elif any(i in config.selected_server['server_description'] for i in name):
                return function
        return None

    def get_vanilla_url(self) -> Tuple[str]:
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

    def get_papermc_url(self) -> Tuple[str]:
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

class Server_API(Server_Versioning, Server_Files):
    """
    Depending on configs, using class inheritance relevant functions will be updated.
    server_console_reachable()
    _send_command()
    _get_status()
    _get_server_version() - From Server_Files

    """

    def __init__(self):
        pass

    # Check if server console is reachable.
    async def server_console_reachable(self) -> bool:
        """
        Check if server console is reachable by sending a unique number to be checked in logs.

        Returns:
            bool: Console reachable.
        """

        if config.get('server_file_access') is True:
            check_command, unique_number = utils.get_check_command()  # Custom command to send with unique number.
            if await self.send_command(check_command) is True:
                if self.read_log(unique_number) is True:  # Check logs for unique number.
                    return True
        return False

    # This will be updated with correct code to send command to server console based on configs.
    def _send_command(self, command: str) -> bool:
        """Placeholder function for sending command to Minecraft server."""

        return False

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

        if self._send_command(command) is True:
            await asyncio.sleep(config.get('command_buffer_time'))
            return True
        return False

    def _get_status(self) -> bool:
        """
        Check server active status by sending unique number, then checking log for it.

        Returns:
            bool: If server reachable.
        """
        pass

    async def get_status(self, force_check: bool = False) -> bool:
        """
        Returns boolean if server is active.
        Depending on configs, prioritizes ping_server(), server_console_reachable(), _get_status()

        Returns:
            bool: If server is active (not same as MC console is reachable).
        """

        if config.get('ping_before_command') is True:
            return self.ping_server()
        # Can force check even if configs disable it.
        elif config.get('check_before_command') is True or force_check is True:
            return await self.server_console_reachable()
        else:
            return self._get_status()

    def read_log(self):
        if not config.get('server_file_access'):
            return False



class Server_Rcon_API(Server_API):
    def server_console_reachable(self) -> bool:
        """
        Check if server console is reachable by sending a unique number.

        Returns:
            bool: Console reachable.
        """

        check_command, unique_number = utils.get_check_command()
        if response := await self.send_command(check_command):
            if unique_number in response:
                return True

    def _send_command(self, command: str) -> Union[str, bool]:
        """
        Send command to server with RCON.

        Args:
            command str: Minecraft server command.

        Returns:
            str, bool: Output from RCON or False if error.
        """

        server_rcon_client = mctools.RCONClient(config.get('server_address'), port=config.get('rcon_port'))
        try: server_rcon_client.login(config.get('rcon_pass'))
        except ConnectionError:
            lprint(f"Error Connecting to RCON: {config.get('server_ip')} : {config.get('rcon_port')}")
            return False
        else:
            return_data = server_rcon_client.command(command)
            server_rcon_client.stop()
            return return_data


class Server_Tmux_API(Server_API):
    def _send_command(self, command: str) -> bool:
        """
        Sends command to Minecraft server console in Tmux session.

        Args:
            command: Command to send.

        Returns:
            bool: If os.system() command was successful (not if MC command was successful).
        """

        if os.system(f"tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} '{command}' ENTER"):
            return False
        return True


class Server_Screen_API(Server_API):
    def _send_command(self, command: str) -> bool:
        """
        Sends command to Minecraft server console in Screen session.

        Args:
            command: Command to send.

        Returns:
            bool: If os.system() command was successful (not if MC command was successful).
        """

        if os.system(f"screen -S {config.get('screen_session_name')} -X stuff '{command}\n'"):
            return False
        return True


class Server_Subprocess_API(Server_API):
    # TODO be able to have multiple subprocess servers running and switch between them
    def _send_command(self, command):
        mc_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
        mc_subprocess.stdin.flush()
