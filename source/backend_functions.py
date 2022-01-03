import subprocess, requests, datetime, asyncio, random, time, csv, os, re
import mctools
from file_read_backwards import FileReadBackwards
from bs4 import BeautifulSoup
from slime_vars import *

server_active = False
discord_channel = None

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

# ========== Extra Functions: start, send command, read log, etc
def lprint(arg1=None, arg2=None):
    """Prints and Logs events in file."""
    if type(arg1) is str:
        msg, user = arg1, 'Script'  # If did not receive ctx object.
    else:
        try: user = arg1.message.author
        except: user = 'N/A'
        msg = arg2

    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({user}): {msg}"
    print(output)

    # Logs output.
    with open(bot_log_file, 'a') as file:
        file.write(output + '\n')

lprint("Server selected: " + server_selected[0])

def format_args(args, return_empty_str=False):
    """
    Formats passed in *args from Discord command functions.
    This is so quotes aren't necessary for Discord command arguments.

    Args:
        args str: Passed in args to combine and return.
        return_empty bool(False): returns empty str if passed in arguments aren't usable for Discord command.

    Returns:
        str: Arguments combines with spaces.
    """

    if args: return ' '.join(args)
    else:
        if return_empty_str is True:
            return ''
        return "No reason given."

def get_datetime():
    """Returns date and time. (2021-12-04 01-49)"""

    return datetime.datetime.now().strftime('%Y-%m-%d %H-%M')

def remove_ansi(text):
    """Removes ANSI escape characters."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def read_json(json_file):
    """Read .json files."""
    os.chdir(bot_files_path)
    with open(server_path + '/' + json_file) as file:
        return [i for i in json.load(file)]

def read_csv(csv_file):
    """Read .csv files."""
    os.chdir(bot_files_path)
    with open(csv_file) as file:
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

def get_public_ip():
    """Gets your public IP address, to updates server ip address varable using request.get()"""

    global server_ip
    server_ip = requests.get('http://ip.42.pl/raw').text
    return server_ip

def channel_set(channel):
    global discord_channel
    discord_channel = channel

async def channel_send(msg):
    if discord_channel: await discord_channel.send(msg)


# ========== Server Commands: start, send command, read log, etc
async def server_command(command, stop_at_checker=True, skip_check=False, discord_msg=True):
    """
    Sends command to Minecraft server. Depending on whether server is a subprocess or in Tmux session or using RCON.
    Sends command to server, then reads from latest.log file for output.
    If using RCON, will only return RCON returned data, can't read from server log.

    Args:
        command str: Command to send.
        stop_at_checker bool(True): Only returns log output under sent status_checker
        skip_check bool(False): Skips server_active boolean check.
        discord_msg bool(True): Send message indicating if server is inactive.

    Returns:
        bool: If error sending command to server, sends False boolean.
        list: Returns list containing match from server_log if found, and random_number used.
    """

    global mc_subprocess, server_active

    async def inactive_msg():
        if discord_msg: await channel_send("**Server INACTIVE** :red_circle:\nUse `?stats` or `?check` to check if server is back online.")

    # This is so user can't keep sending commands to RCON if server is unreachable. Use ?stat or ?check to actually check if able to send command to server.
    # Without this, the user might try sending multiple commands to a unreachable RCON server which will hold up the bot.
    if not skip_check and not server_active:
        await inactive_msg()
        return False

    status_checker_command, random_number = 'locatebiome ', str(random.random())
    status_checker = status_checker_command + random_number

    if use_rcon is True:
        if ping_server():
            return [await server_rcon(command), None]
        else: return False

    elif use_subprocess is True:
        if mc_subprocess is not None:
            mc_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
            mc_subprocess.stdin.flush()
        else:
            await inactive_msg()
            return False

    elif use_tmux is True:
        # Checks if server is active in the first place by sending random number to be matched in server log.
        os.system(f'tmux send-keys -t {tmux_session_name}:0.0 "{status_checker}" ENTER')
        await asyncio.sleep(1)
        if not server_log(random_number):
            await inactive_msg()
            return False
        os.system(f'tmux send-keys -t {tmux_session_name}:0.0 "{command}" ENTER')

    else:
        await inactive_msg()
        return False

    time.sleep(1)
    return_data = [server_log(command), None]
    if stop_at_checker is True:
        return_data[1] = random_number
    return return_data

async def zomboid_command(command):
    """Sends command to tmux 0.1 Project Zomboid server."""

    os.system(f'tmux send-keys -t {tmux_session_name}:0.1 "{command}" ENTER')

def zomboid_log(lines=5):
    """
    """

    file_path = '/home/0n1udra/Zomboid/server-console.txt'
    log_data = ''
    with FileReadBackwards(file_path) as file:
        for i in range(lines):

            log_data += file.readline()
            print(log_data.strip())

        if log_data: return '\n'.join(list(reversed(log_data.split('\n'))))[1:]

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

    server_rcon_client = mctools.RCONClient(server_ip, port=rcon_port)
    try: server_rcon_client.login(rcon_pass)
    except ConnectionError:
        lprint(f"Error Connecting to RCON: {server_ip} : {rcon_port}")
        server_active = False
        return False
    else:
        server_active = True
        return_data = server_rcon_client.command(command)
        server_rcon_client.stop()
        return return_data

async def server_status(discord_msg=False):
    """
    Gets server active status, by sending command to server and checking server log.

    Returns:
        bool: returns True if server is online.
    """

    global server_active

    if discord_msg: await channel_send('***Checking Server Status...***')
    lprint("Checking server active status...")

    # Creates random number to send in command, server is online if match is found in log.
    response = await server_command(' ', skip_check=True, stop_at_checker=True, discord_msg=discord_msg)
    if response:
        if discord_msg: await channel_send("**Server ACTIVE** :green_circle:")
        lprint("Server Status: Active")
        server_active = True
        return True
    else:
        # server_command will send a discord message if server is inactive, so it's unneeded here.
        lprint("Server Status: Inactive")
        server_active = False

def server_log(match=None, file_path=None, lines=50, normal_read=False, log_mode=False, filter_mode=False, match_lines=10, stopgap_str=None, return_reversed=False):
    """
    Read latest.log file under server/logs folder. Can also find match.
    What a fat ugly function you are :(

    Args:
        match str: Check for matching string.
        file_path str(None): File to read. Defaults to server's latest.log
        lines int(15): Number of most recent lines to return.
        log_mode bool(False): Return x lines from log file, skips matching.
        list_mode bool(False): Puts log lines in a list instead of single string.
        normal_read bool(False): Reads file top down, defaults to bottom up using file-read-backwards module.
        filter_mode bool(False): Don't stop at first match.
        match_lines int(10): How many matches to find.
        return_reversed bool(False): Returns so ordering is newest at bottom going up for older.

    Returns:
        log_data (str): Returns found match log line or multiple lines from log.
    """

    if match is None: match = 'placeholder_match'
    match = match.lower()

    if stopgap_str is None: stopgap_str = 'placeholder_stopgap'
    stopgap_str = stopgap_str.lower()

    # Defaults file to server log.
    if file_path is None: file_path = f"{server_path}/logs/latest.log"
    if not os.path.isfile(file_path): return False

    if filter_mode is True: lines = log_lines_limit

    log_data = ''
    if normal_read:
        with open(file_path, 'r') as file:
            for line in file:
                if match in line: return line
    else:
        with FileReadBackwards(file_path) as file:
            for i in range(lines):
                line = file.readline()
                if 'banlist' in match:  # How ugly :(
                    if 'was banned by' in line:  # finds log lines that shows banned players.
                        log_data += line
                    elif ']: There are' in line:  # finds the end so it doesn't return everything from log other then banned users.
                        log_data += line
                        break
                elif log_mode:
                    log_data += line
                elif match in line.lower():
                    log_data += line
                    if filter_mode is True and match_lines >= 1:
                        match_lines -= 1
                    else: break
                if stopgap_str.lower() in line.lower(): break

    if log_data:
        if return_reversed is True:
            log_data = '\n'.join(list(reversed(log_data.split('\n'))))[1:]  # Reversed line ordering, so most recent lines are at bottom.
        return log_data

def server_start():
    """
    Start Minecraft server depending on whether you're using Tmux subprocess method.

    Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

    Returns:
        bool: If successful boot.
    """

    global mc_subprocess

    os.chdir(server_path)
    if use_subprocess is True:
        # Runs MC server as subprocess. Note, If this script stops, the server will stop.
        try:
            mc_subprocess = subprocess.Popen(server_selected[2].split(), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except: lprint("Error server starting subprocess")

        if type(mc_subprocess) == subprocess.Popen: return True

    elif use_tmux is True:
        os.system(f'tmux send-keys -t {tmux_session_name}:0.0 "cd /" ENTER')  # Fix: 'java.lang.Error: Properties init: Could not determine current working' error
        os.system(f'tmux send-keys -t {tmux_session_name}:0.0 "cd {server_path}" ENTER')

        # Tries starting new detached tmux session.
        if not os.system(f'tmux send-keys -t {tmux_session_name}:0.0 "{server_selected[2]}" ENTER'):
            return True
    else: return "Error starting server."

def server_version():
    """
    Gets server version, either by reading server log or using PINGClient.

    Returns:
        str: Server version number.
    """

    if use_rcon is True:
        try: return ping_server()['version']['name']
        except: return 'N/A'
    elif server_files_access is True:
        returned_data = edit_file('version')[1]
        if 'not' not in returned_data:
            return returned_data
    return 'N/A'

def server_motd():
    """
    Gets current message of the day from server, either by reading from server.properties file or using PINGClient.

    Returns:
        str: Server motd.
    """

    if server_files_access is True:
        return edit_file('motd')[1]
    elif use_rcon is True:
        return remove_ansi(ping_server()['description'])
    else: return "N/A"

def ping_server():
    """
    Gets server information using mctools.PINGClient()

    Returns:
        dict: Dictionary containing 'version', and 'description' (motd).

    """

    global server_active

    try:
        ping = mctools.PINGClient(server_ip)
        stats = ping.get_stats()
        ping.stop()
    except ConnectionRefusedError:
        lprint("Ping Error")
        server_active = False
        return False
    else:
        server_active = True
        return stats

def ping_url():
    """Checks if server_url address works by pinging it twice."""

    ping = subprocess.Popen(['ping', '-c', '2', server_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ping_out, ping_error = ping.communicate()
    if server_ip in str(ping_out):
        return 'working'
    return 'inactive'

def check_latest_version():
    """
    Gets latest Minecraft server version number from official website using bs4.

    Returns:
        str: Latest version number.
    """

    soup = BeautifulSoup(requests.get(new_server_url).text, 'html.parser')
    for i in soup.findAll('a'):
        if i.string and 'minecraft_server' in i.string:
            return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.

def get_latest_version():
    """
    Downloads latest server.jar file from Minecraft website. Also updates eula.txt.

    Returns:
        bool: If download was successful.
    """

    os.chdir(mc_path)
    jar_download_url = ''

    minecraft_website = requests.get(new_server_url)
    soup = BeautifulSoup(minecraft_website.text, 'html.parser')
    # Finds Minecraft server.jar urls in div class.
    div_agenda = soup.find_all('div', class_='minecraft-version')
    for i in div_agenda[0].find_all('a'):
        jar_download_url = f"{i.get('href')}"

    if not jar_download_url: return False

    # Saves new server.jar in current server.
    new_jar_data = requests.get(jar_download_url).content

    try:
        with open(server_path + '/eula.txt', 'w+') as f:
            f.write(new_jar_data)
    except IOError:
        lprint(f"Error updatine eula.txt file: {server_path}")

    try:
        with open(server_path + '/server.jar', 'wb+') as f:
            f.write(new_jar_data)
        return True
    except IOError:
        lprint(f"Error saving new jar file: {server_path}")

    return False

async def get_player_list():
    response = await server_command("list")
    if not response: return False

    # Gets data from RCON response or reads server log for line containing player names.
    if use_rcon is True: log_data = response
    else:
        await asyncio.sleep(1)
        log_data = server_log('players online')

    if not log_data: return False

    log_data = log_data.split(':')  # [23:08:55 INFO]: There are 2 of a max of 20 players online: R3diculous, MysticFrogo
    text = log_data[-2]  # There are 2 of a max of 20 players online
    player_names = log_data[-1]  # R3diculous, MysticFrogo
    # If there's no players active, player_names will still contain some anso escape characters.
    if len(player_names.strip()) < 5: return None
    else:
        player_names = [f"{i.strip()[:-4]}\n" if use_rcon else f"{i.strip()}" for i in (log_data[-1]).split(',')]
        # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
        #player_names_discord = [f"`{i.strip()[:-4]}`\n" if use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]

        return player_names, text

async def get_location(player=''):
    """Gets player's location coordinates."""

    if response := await server_command(f"data get entity {player} Pos"):
        log_data = server_log('entity data', stopgap_str=response[1])
        # ['', '14:38:26] ', 'Server thread/INFO]: R3diculous has the following entity data: ', '-64.0d, 65.0d, 16.0d]\n']
        # Removes 'd' and newline character to get player coordinate. '-64.0 65.0 16.0d'
        if log_data:
            location = log_data.split('[')[3][:-3].replace('d,', '')
            return location


# ========== Backup/Restore.
def edit_file(target_property=None, value='', file_path=f"{server_path}/server.properties"):
    """
    Edits server.properties file if received target_property and value. Edits inplace with fileinput
    If receive no value, will return current set value if property exists.

    Args:
        target_property str(None): Find Minecraft server property.
        value str(''): If received argument, will change value.
        file_path str(server.properties): File to edit. Must be in .properties file format. Default is server.properties file under /server folder containing server.jar.

    Returns:
        str: If target_property was not found.
        tuple: First item is line from file that matched target_property. Second item is just the current value.
    """

    os.chdir(server_path)
    return_line = discord_return = ''  # Discord has it's own return variable, because the data might be formatted for Discord.

    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)

            if target_property == 'all':  # Return all lines of file.
                discord_return += F"`{line.rstrip()}`\n"
                return_line += line.strip() + '\n'
                print(line, end='')

            # If found match, and user passed in new value to update it.
            elif target_property in split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value
                    new_line = '='.join(split_line)
                    discord_return = f"Updated Property:`{line}` > `{new_line}`.\nRestart to apply changes."
                    return_line = line
                    print(new_line, end='\n')
                # If user did not pass a new value to update property, just return the line from file.
                else:
                    discord_return = f"`{'='.join(split_line)}`"
                    return_line = '='.join(split_line)
                    print(line, end='')
            else: print(line, end='')

    if return_line:
        return return_line, return_line.split('=')[1].strip()
    else: return "Match not found.", 'Match not found.'

def get_from_index(path, index):
    """
    Get server or world backup folder name from passed in index number

    Args:
        path str: Location to find world or server backups.
        index int: Select specific folder, get index from other functions like ?worldbackupslist, ?serverbackupslist

    Returns:
            str: file path of selected folder.
    """

    return os.listdir(path)[index]

def fetch_backups(path):
    """
    Gets x amount of backups. Usually to show in list.

    Args:
        path str: Path of world or server backups location.
    """

    backups = []
    if not os.path.isdir(path): return False

    for index, item in enumerate(os.listdir(path)):
        if os.path.isdir(path + '/' + item):
            backups.append([index, item])
    return backups

def create_backup(name, src, dst):
    """
    Create a new world or server backup, by copying and renaming folder.

    Args:
        name str: Name of new backup. Final name will have date and time prefixed.
        src str: Folder to backup, whether it's a world folder or a entire server folder.
        dst str: Destination for backup.
    """

    if not os.path.isdir(dst): os.makedirs(dst)

    version = f"{'v(' + server_version() + ') ' if 'N/A' not in server_version() else ''}"
    new_name = f"({get_datetime()}) {version}{name}"
    new_backup_path = dst + '/' + new_name.strip()
    shutil.copytree(src, new_backup_path)

    if os.path.isdir(new_backup_path):
        lprint("Backed up to: " + new_backup_path)
        return new_name
    else:
        lprint("Error creating backup at: " + new_backup_path)
        return False

def restore_backup(src, dst, reset=False):
    """
    Restores world or server backup. Overwrites existing files.

    Args:
        src str: Backed up folder to copy to current server.
        dst str: Location to copy backup to.
        reset bool(False): Leave src folder empty and not copy backup to dst.
    """

    try: shutil.rmtree(dst)
    except: pass

    # Used in ?worldreset and ?serverreset Discord command to clear all world or server files.
    if reset is True: return True

    try:
        shutil.copytree(src, dst)
        return True
    except: lprint("Error restoring: " + str(src + ' > ' + dst))

def delete_backup(backup):
    """
    Delete world or server backup.

    Args:
        backup str: Path of backup to delete.
    """

    try:
        shutil.rmtree(backup)
        return True
    except: lprint("Error deleting: " + str(backup))


# ========== Discord Commands.
def get_server_from_index(index):
    """Returns server backup full path from passed in index number."""
    return get_from_index(server_backups_path, index)

def get_world_from_index(index):
    return get_from_index(world_backups_path, index)

def fetch_servers():
    """Returns list of x number of backed up server."""
    return fetch_backups(server_backups_path)

def fetch_worlds():
    return fetch_backups(world_backups_path)

def backup_server(name='server_backup'):
    """Create new server backup with specified name."""
    return create_backup(name, server_path, server_backups_path)

def backup_world(name="world_backup"):
    return create_backup(name, server_path + '/world', world_backups_path)

def delete_server(server):
    """Delete specified server with specified index."""
    return delete_backup(server_backups_path + '/' + server)

def delete_world(world):
    return delete_backup(world_backups_path + '/' + world)

def restore_server(server=None, reset=False):
    """Restore server with specified index."""
    os.chdir(server_backups_path)
    return restore_backup(server, server_path, reset)

def restore_world(world=None, reset=False):
    os.chdir(world_backups_path)
    return restore_backup(world, server_path + '/world', reset)
