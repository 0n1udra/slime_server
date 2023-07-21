import subprocess, platform, requests, asyncio, shutil, random, json, os, re
import mctools
from os.path import join
from file_read_backwards import FileReadBackwards
from bot_files.slime_vars import config
from bot_files.extra import lprint
from bot_files.server_api import Server_Screen_API, Server_Subprocess_API, Server_Rcon_API, Server_Tmux_API
import bot_files.extra as extra
from bs4 import BeautifulSoup
#from bot_files.extra import *


# Used for removing ANSI escape characters
find_ansi = re.compile(r'\x1b[^m]*m')
ctx = 'backend_functions.py'


class Backend:
    server_api_types = {'use_rcon': Server_Rcon_API, 'use_tmux': Server_Tmux_API, 'use_screen': Server_Screen_API}

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

    def _update_server_api(self):
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

    def get_server(self, server_name):
        """
        Get configs dictionary of specific server by name.

        Args:
            server_name str: Name of server to get configs of.

        Returns:
            dict: Configs dict of specified server.
        """
        if server_name in config.servers:
            return config.servers[server_name]
        else: return False


    # File reading and writing
    def read_server_log(self, match=None, match_list=[], file_path=None, lines=15, normal_read=False, log_mode=False, filter_mode=False, stopgap_str=None, return_reversed=False):
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
                if target_property in split_line[0] and len(split_line) > 1:
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


    def download_latest():
        """
        Downloads latest server.jar file from Minecraft website. Also updates eula.txt.

        Returns:
            bool: If download was successful.
        """

        os.chdir(config.get('mc_path'))
        jar_download_url = version_info = ''

        def check(type):
            """Checks if specific keywords in server name and description."""
            sserver = config.get('selected_server')
            return True if type in (sserver['name'].lower(), sserver['description'].lower()) else False

        if check('vanilla'):
            def request_json(url): return json.loads(requests.get(url).text)

            # Finds latest release from manifest and gets required data.
            manifest = request_json('https://launchermeta.mojang.com/mc/game/version_manifest.json')
            for i in manifest['versions']:
                if i['type'] == 'release':
                    version_info = f"{i['id']} ({i['time']})"
                    jar_download_url = request_json(i['url'])['downloads']['server']['url']
                    break  # Breaks loop on firest release found (should be latest).

        if check('papermc'):
            base_url = 'https://papermc.io/api/v2/projects/paper'

            # Extracts required data for download URL. PaperMC API: https://papermc.io/api/docs/swagger-ui/index.html?configUrl=/api/openapi/swagger-config
            def get_data(find, url=''): return json.loads(requests.get(f'{base_url}{url}').text)[find]
            latest_version = get_data('versions')[-1]  # Gets latest Minecraft version (e.g. 1.18.2).
            latest_build = get_data('builds', f'/versions/{latest_version}')[-1]  # Get PaperMC Paper latest build (277).
            # Get file name to download (paper-1.18.2-277.jar).
            latest_jar = version_info = get_data('downloads', f'/versions/{latest_version}/builds/{latest_build}')['application']['name']
            # Full download URL: https://papermc.io/api/v2/projects/paper/versions/1.18.2/builds/277/downloads/paper-1.18.2-277.jar
            jar_download_url = f'{base_url}/versions/{latest_version}/builds/{latest_build}/downloads/{latest_jar}'

        if not jar_download_url:
            lprint(ctx, "ERROR: Issue downloading new jar")
            return False

        # Saves new server.jar in current server.
        new_jar_data = requests.get(jar_download_url).content

        try:  # Sets eula.txt file.
            with open(config.get('server_path') + '/eula.txt', 'w+') as f: f.write('eula=true')
        except IOError: lprint(ctx, f"Errorr: Updating eula.txt file: {config.get('server_path')}")

        try:  # Saves file as server.jar.
            with open(config.get('server_path') + '/server.jar', 'wb+') as f: f.write(new_jar_data)
        except IOError: lprint(ctx, f"ERROR: Saving new jar file: {config.get('server_path')}")
        else: return version_info, jar_download_url

        return False

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
        elif config.get('windows_compatibility') is True and platform.system() == 'Windows':
            os.chdir(config.get('server_path'))
            subprocess.Popen(config.get('windows_cmdline_start') + config.get('server_launch_command'), shell=True)

        elif config.get('use_tmux') is True:
            os.system(f"tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} 'cd {config.get('server_path')}' ENTER")

            # Starts server in tmux pane.
            if not os.system(f'tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} "{config.get('server_launch_command')}" ENTER'):
                return True
        else: return False

    def check_latest():
        """
        Gets latest Minecraft server version number from official website using bs4.

        Returns:
            str: Latest version number.
        """

        soup = BeautifulSoup(requests.get(config.get('new_server_address')).text, 'html.parser')
        for i in soup.findAll('a'):
            if i.string and 'minecraft_server' in i.string:
                return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.


    async def server_status(discord_msg=False):
        """
        Gets server active status, by sending command to server and checking server log.

        Returns:
            bool: returns True if server is online.
        """

        global server_active

        lprint(ctx, "Checking Minecraft server status...")

        # send_command() will send random number, server is online if match is found in log.
        response = await send_command(' ', discord_msg=discord_msg, force_check=True, ctx=ctx)
        if response:
            server_active = True
            lprint(ctx, "Server Status: Active")
            return True
        elif response is None:
            # Means server status is unreachable but still want to be able to send commands.
            server_active = None
            lprint(ctx, "Server Status: N/A")
            return None
        else:
            server_active = False
            lprint(ctx, "Server Status: Inactive")


backend = Backend()
# ========== Server Commands: start, send command, read log, etc

