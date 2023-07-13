import discord, requests, asyncio, psutil, random
from file_read_backwards import FileReadBackwards
from bs4 import BeautifulSoup
from bot_files.extra import *
from os.path import join
import bot_files.slime_vars as slime_vars
if slime_vars.use_rcon: import mctools
if slime_vars.windows_cmdline_start: import subprocess

# Remove ANSI escape characters
import re
text = 'ls\r\n\x1b[00m\x1b[01;31mexamplefile.zip\x1b[00m\r\n\x1b[01;31m'
reaesc = re.compile(r'\x1b[^m]*m')

ctx = 'backend_functions.py'
bot = None
server_active = None
discord_channel = None
slime_proc = slime_pid = None  # If using nohup to run bot in background.


# ========== Discord Bot
def set_slime_proc(proc, pid):
    global slime_proc, slime_pid
    slime_proc, slime_pid = proc, pid

def channel_set(channel):
    """Sets discord_channel global variable."""
    global discord_channel
    discord_channel = channel

async def channel_send(msg):
    """Send message to discord_channel."""

    if discord_channel: await discord_channel.send(msg)

# ========== Server Commands: start, send command, read log, etc
def server_log(match=None, match_list=[], file_path=None, lines=15, normal_read=False, log_mode=False, filter_mode=False, stopgap_str=None, return_reversed=False):
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

    # Parameter setups.
    if match is None: match = 'placeholder_match'
    match = match.lower()
    if stopgap_str is None: stopgap_str = 'placeholder_stopgap'
    # Defaults file to server log.
    if file_path is None: file_path = slime_vars.server_log_file
    if not os.path.isfile(file_path): return False

    log_data = ''

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
            while i < lines and total < line_count and total <= slime_vars.log_lines_limit:
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

async def send_command(command, force_check=False, skip_check=False, discord_msg=True, ctx=None):
    """
    Sends command to Minecraft server. Depending on whether server is a subprocess or in Tmux session or using RCON.
    Sends command to server, then reads from latest.log file for output.
    If using RCON, will only return RCON returned data, can't read from server log.

    Args:
        command str: Command to send.
        force_check bool(False): Skips server_active boolean check, send command anyways.
        skip_check(False): Skips sending check command. E.g. For sending a lot of consecutive commands, to help reduces time.
        discord_msg bool(True): Send message indicating if server is inactive.

    Returns:
        bool: If error sending command to server, sends False boolean.
        list: Returns list containing match from server_log if found, and random_number used.
    """

    global mc_subprocess, server_active

    status = None

    # This is so user can't keep sending commands to RCON if server is unreachable. Use ?stat or ?check to actually check if able to send command to server.
    # Without this, the user might try sending multiple commands to an unreachable RCON server which will hold up the bot.
    if force_check is False and server_active is False: status = False

    # Create random number to send to server to be checked in logs.
    status_checker_command, random_number = slime_vars.status_checker_command, str(random.random())
    status_checker = status_checker_command + ' ' + random_number

    if slime_vars.use_rcon is True:
        if server_ping():
            return [await server_rcon(command), None]
        else: status = False

    elif slime_vars.use_subprocess is True:
        if mc_subprocess is not None:
            mc_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
            mc_subprocess.stdin.flush()
        else: status = False

    elif slime_vars.use_tmux is True or slime_vars.server_use_screen:
        if slime_vars.enable_status_checker is False: skip_check = True  # Don't send the 'xp' command.

        if not skip_check:  # Check if server reachable before sending command.
            # Checks if server is active in the first place by sending random number to be matched in server log.
            if slime_vars.server_use_screen:  # Using screen to run/send commands to MC server.
                os.system(f'screen -S {slime_vars.screen_session_name} -X stuff "{status_checker}\n"')
            else: os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_minecraft_pane} "{status_checker}" ENTER')
            await asyncio.sleep(slime_vars.command_buffer_time)
            if not server_log(random_number): status = False

        if slime_vars.server_use_screen:
            os.system(f'screen -S {slime_vars.screen_session_name} -X stuff "{command}\n"')
        else: os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_minecraft_pane} "{command}" ENTER')

    else: status = False

    if slime_vars.enable_status_checker is False: return None
    if status is False:
        msg = "**Server INACTIVE** :red_circle:\nUse `?check` to update server status."
        if discord_msg:
            try: await ctx.send(msg)
            except: await channel_send(msg)
        return False

    await asyncio.sleep(slime_vars.command_buffer_time)
    # Returns log line that matches command.
    return_data = [server_log(command), random_number]
    # needs to return None because bot can't accurately get feedback.
    return return_data

async def server_rcon(command=''):
    """
    Send command to server with RCON.

    Args:
        command str(''): Minecraft server command.

    Returns:
        bool: Returns False if error connecting to RCON.
        str: Output from RCON.
    """

    global server_active

    server_rcon_client = mctools.RCONClient(slime_vars.server_address, port=slime_vars.rcon_port)
    try: server_rcon_client.login(slime_vars.rcon_pass)
    except ConnectionError:
        lprint(ctx, f"Error Connecting to RCON: {slime_vars.server_ip} : {slime_vars.rcon_port}")
        server_active = False
        return False
    else:
        server_active = True
        return_data = server_rcon_client.command(command)
        server_rcon_client.stop()
        return return_data

async def server_status(ctx=None):
    """
    Gets server active status, by sending command to server and checking server log.

    Returns:
        bool: returns True if server is online.
    """

    global server_active

    lprint(ctx, "Checking Minecraft server status...")

    # send_command() will send random number, server is online if match is found in log.
    response = await send_command(' ', force_check=True, ctx=ctx)
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
        return False

def server_start():
    """
    Start Minecraft server depending on whether you're using Tmux subprocess method.

    Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

    Returns:
        bool: If successful boot.
    """

    global mc_subprocess

    if slime_vars.server_use_screen is True:
        os.chdir(slime_vars.server_path)
        if not os.system(f'screen -dmS "{slime_vars.screen_session_name}" {slime_vars.server_selected[2]}'):
            return True
        else: return False

    elif slime_vars.use_subprocess is True:
        # Runs MC server as subprocess. Note, If this script stops, the server will stop.
        try:
            mc_subprocess = subprocess.Popen(slime_vars.server_selected[2].split(), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except: lprint(ctx, "Error server starting subprocess")

        if type(mc_subprocess) == subprocess.Popen: return True

    # Start java server using subprocess and cmd's start command.
    elif slime_vars.windows_cmdline_start:
        os.chdir(slime_vars.server_path)
        subprocess.Popen(slime_vars.windows_cmdline_start + slime_vars.server_launch_command, shell=True)

    elif slime_vars.use_tmux is True:
        os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_minecraft_pane} "cd {slime_vars.server_path}" ENTER')

        # Starts server in tmux pane.
        if not os.system(f'tmux send-keys -t {slime_vars.tmux_session_name}:{slime_vars.tmux_minecraft_pane} "{slime_vars.server_selected[2]}" ENTER'):
            return True
    else: return False

def server_version():
    """
    Gets server version, either by reading server log or using PINGClient.

    Returns:
        str: Server version number.
    """

    if slime_vars.use_rcon is True:
        try: return server_ping()['version']['name']
        except: return 'N/A'
    elif slime_vars.server_files_access is True:
        try: return server_log('server version').split('version')[1].strip()
        except: return 'N/A'
    return 'N/A'

def server_motd():
    """
    Gets current message of the day from server, either by reading from server.properties file or using PINGClient.

    Returns:
        str: Server motd.
    """

    if slime_vars.server_files_access is True:
        return edit_file('motd')[1]
    elif slime_vars.use_rcon is True:
        return remove_ansi(server_ping()['description'])
    else: return "N/A"

def server_ping():
    """
    Gets server information using mctools.PINGClient()

    Returns:
        dict: Dictionary containing 'version', and 'description' (motd).
    """

    global server_active

    try:
        ping = mctools.PINGClient(slime_vars.server_address, slime_vars.server_port)
        stats = ping.get_stats()
        ping.stop()
    except ConnectionRefusedError:
        lprint(ctx, "Ping Error")
        server_active = False
        return False
    else:
        server_active = True
        return stats

def check_latest():
    """
    Gets latest Minecraft server version number from official website using bs4.

    Returns:
        str: Latest version number.
    """

    soup = BeautifulSoup(requests.get(slime_vars.new_server_address).text, 'html.parser')
    for i in soup.findAll('a'):
        if i.string and 'minecraft_server' in i.string:
            return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.

def download_latest():
    """
    Downloads latest server.jar file from Minecraft website. Also updates eula.txt.

    Returns:
        bool: If download was successful.
    """

    os.chdir(slime_vars.mc_path)
    jar_download_url = version_info = ''

    if 'vanilla' in slime_vars.server_selected[0].lower():
        def request_json(url): return json.loads(requests.get(url).text)

        # Finds latest release from manifest and gets required data.
        manifest = request_json('https://launchermeta.mojang.com/mc/game/version_manifest.json')
        for i in manifest['versions']:
            if i['type'] == 'release':
                version_info = f"{i['id']} ({i['time']})"
                jar_download_url = request_json(i['url'])['downloads']['server']['url']
                break  # Breaks loop on firest release found (should be latest).

    if 'papermc' in slime_vars.server_selected[0].lower():
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
        with open(slime_vars.server_path + '/eula.txt', 'w+') as f: f.write('eula=true')
    except IOError: lprint(ctx, f"Errorr: Updating eula.txt file: {slime_vars.server_path}")

    try:  # Saves file as server.jar.
        with open(slime_vars.server_path + '/server.jar', 'wb+') as f: f.write(new_jar_data)
    except IOError: lprint(ctx, f"ERROR: Saving new jar file: {slime_vars.server_path}")
    else: return version_info, jar_download_url

    return False

async def get_players():
    """Extracts wanted data from output of 'list' command."""

    response = await send_command("list")
    if not response: return False

    # Gets data from RCON response or reads server log for line containing player names.
    if slime_vars.use_rcon is True: log_data = response[0]
    else:
        await asyncio.sleep(1)
        log_data = server_log('players online')

    if not log_data: return False

    # Use regular expression to extract player names
    log_data = log_data.split(':')  # [23:08:55 INFO]: There are 2 of a max of 20 players online: R3diculous, MysticFrogo
    text = log_data[-2]  # There are 2 of a max of 20 players online
    text = reaesc.sub('', text)
    player_names = log_data[-1]  # R3diculous, MysticFrogo
    # If there's no players active, player_names will still contain some anso escape characters.
    if len(player_names.strip()) < 5: return None
    else:

        player_names = [f"{i.strip()[:-4]}\n" if slime_vars.use_rcon else f"{i.strip()}" for i in (log_data[-1]).split(',')]
        # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
        # player_names_discord = [f"`{i.strip()[:-4]}`\n" if use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]
        new = []
        for i in player_names:
            x = reaesc.sub('', i).strip().replace('[3', '')
            x = x.split(' ')[-1]
            x = x.replace('\\x1b', '').strip()
            new.append(x)
        player_names = new
        return player_names, text

async def get_coords(player=''):
    """Gets player's location coordinates."""

    if response := await send_command(f"data get entity {player} Pos", skip_check=True):
        log_data = server_log('entity data', stopgap_str=response[1])
        # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
        # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
        if log_data:
            location = log_data.split('[')[-1][:-3].replace('d', '')
            return location


# ========== Servers and backups
def new_server(name):
    """
    Create a new world or server backup, by copying and renaming folder.

    Args:
        new_name str: Name of new copy. Final name will have date and time prefixed.
        src str: Folder to backup, whether it's a world folder or a entire server folder.
        dst str: Destination for backup.
    """

    new_folder = join(slime_vars.servers_path, name.strip())
    os.mkdir(new_folder)
    return new_folder

def new_backup(new_name, src, dst, exact=slime_vars.exact_foldername):
    """
    Create a new world or server backup, by copying and renaming folder.

    Args:
        new_name str: Name of new copy. Final name will have date and time prefixed.
        src str: Folder to backup, whether it's a world folder or a entire server folder.
        dst str: Destination for backup.
    """

    if not os.path.isdir(dst): os.makedirs(dst)
    # TODO add multiple world folders backup
    # folder name: version tag if known, date, optional name
    version = f"{'v(' + server_version() + ') ' if 'N/A' not in server_version() else ''}"
    new_name = f"({get_datetime()}) {version}{new_name}"
    new_backup_path = join(dst, new_name.strip())
    shutil.copytree(src, new_backup_path)
    return new_backup_path

def restore_backup(src, dst):
    """
    Restores world or server backup. Overwrites existing files.

    Args:
        src str: Backed up folder to copy to current server.
        dst str: Location to copy backup to.
    """

    shutil.rmtree(dst)
    shutil.copytree(src, dst)
