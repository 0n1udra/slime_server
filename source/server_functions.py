import subprocess, requests, datetime, random, asyncio, time, csv, os
from file_read_backwards import FileReadBackwards
from bs4 import BeautifulSoup

server_functions_path = os.getcwd()
bot_token_file = '/home/slime/mc_bot_token.txt'

# Run Minecraft server using subprocess.Popen(). Note, If script halts the server will halt also. Useful if you can't get Tmux, but I recommend Tmux if you can.
# If use_tmux is also True, script will prioritize use_subprocess. Which means if both vars are True, MC server will run as subprocess instead of running in separate Tmux pane.
# And if use_rcon is also True, RCON capabilities will have top priority over Popen() and Tmux.
use_subprocess = False

# If you have local access to server files but not using Tmux, use RCON to send commands to server. You won't be able to use some features like reading server logs.
use_rcon = False
mc_ip = 'arcpy.asuscomm.com'
rcon_port = 25575
rcon_pass = 'SlimeySlime'

# Local file access allows for server files/folders manipulation for features like backup/restore world saves, editing server.properties file, and read server log.
server_files_access = True
# This is where Minecraft server, world backups and server backups will be saved, so make sure this is a full path and is where you want it.
mc_path = '/mnt/c/Users/DT/Desktop/MC'

# These don't have to be changed.
server_path = f"{mc_path}/server"
world_backups_path = f"{mc_path}/world_backups"
server_backups_path = f"{mc_path}/server_backups"
bot_log_file = f"{server_functions_path}/bot_log.txt"

# Use Tmux to send commands to server. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features like world backup/restore.
use_tmux = True
java_command = f'java -Xmx2G -Xms1G -jar {server_path}/server.jar nogui'  # Update server.jar execution argument for your setup if needed.

if use_rcon: import mctools, re
if server_files_access: import shutil, fileinput, json

new_server_url = 'https://www.minecraft.net/en-us/download/server'
mc_active_status = False
mc_subprocess = None

# Outputs and logs used bot commands and which Discord user invoked them.
def lprint(arg1=None, arg2=None):
    if type(arg1) is str: msg, user = arg1, 'Script'  # If did not receive ctx object.
    else:
        try: user = arg1.message.author
        except: user = 'N/A'
        msg = arg2
    output = f"{datetime.datetime.now()} | ({user}) {msg}"
    print(output)
    with open(bot_log_file, 'a') as file: file.write(output + '\n')

# ========== Server command, start, bot start.
def mc_start():
    """
    Start Minecraft server depending on whether you're using Tmux subprocess method.

    Note: Priority is given to subprocess method over Tmux if both corresponding booleans are True.

    Returns:
        bool: If successful boot.
        str: If error starting server.
    """

    global mc_subprocess
    os.chdir(server_path)
    if use_subprocess:
        # Runs MC server as subprocess. Note, If this script stops, the server will stop.
        try: mc_subprocess = subprocess.Popen(java_command.split(), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except: lprint("Error server starting subprocess")
        if type(mc_subprocess) == subprocess.Popen: return True
    elif use_tmux:
        os.system('tmux send-keys -t mcserver:1.0 "cd /" ENTER')  # Fix: 'java.lang.Error: Properties init: Could not determine current working' error
        os.system(f'tmux send-keys -t mcserver:1.0 "cd {server_path}" ENTER')
        if not os.system(f'tmux send-keys -t mcserver:1.0 "{java_command}" ENTER'): return True # Tries starting new detached tmux session.
    else: return "Error starting server."

# Sends command to tmux window running server.
async def mc_command(command, match_output=None, return_bool=True):
    """
    Sends command to Minecraft server. Depending on whether server is a subprocess or in Tmux session or using RCON.
    Sends command to server, then reads from latest.log file for output.
    If using RCON, will only return RCON returned data, can't read from server log.

    Args:
        command: Command to send.
        match_output [Optional]: Look for specific string from server output.
        return_bool: Return True/False whether or not command ran successfully.

    Returns:
        bool: If error sending command to server, sends False boolean.
        str: Returns matched string if match found.
    """

    global mc_subprocess
    if use_rcon:
        return mc_rcon(command)
    elif use_subprocess:
        if mc_subprocess is not None:
            mc_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
            mc_subprocess.stdin.flush()
        else: return False
    elif use_tmux:
        if os.system(f'tmux send-keys -t mcserver:1.0 "/{command}" ENTER') != 0:
            return True
    else: return "Can't send command to server."

    time.sleep(1)
    if match_output is None:
        if return_bool: return mc_log(command, return_bool=True)
        return mc_log(command)
    else: return mc_log(match_output)

# Send commands to server using RCON.
def mc_rcon(command=''):
    """
    Send command to server with RCON.

    Args:
        command: Minecraft command.

    Returns:
        bool: Returns False if error connecting to RCON.
        str: Output from RCON.
    """

    mc_rcon_client = mctools.RCONClient(mc_ip, port=rcon_port)
    try: mc_rcon_client.login(rcon_pass)
    except ConnectionError:
        lprint(f"Error Connecting to RCON: {mc_ip} : {rcon_port}")
        return False
    else: return mc_rcon_client.command(command)


# ========== Fetching server data, output, ping, reading files.
# Removes unwanted ANSI escape characters.
def remove_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Gets server output by reading log file, can also find response from command in log by finding matching string.
def mc_log(match='placeholder match', file_path=f"{server_path}/logs/latest.log", lines=15, normal_read=False, return_bool=False, log_mode=False):
    """
    Read latest.log file under /logs folder.

    Args:
        match [Optional]: Check for match string.
        file_path [Optional]: Default is latest.log file.
        lines [Optional]: Number of most recent lines to return. Returns 15 lines by default.
        normal_read [Optional]: Reads file top down, by default this function reads file backwards with file-read-backwards module.
        return_bool [Optional]: Return True/False boolean if match was found.

    Returns:

    """
    if not os.path.isfile(file_path): return False

    log_data = ''
    if normal_read:
        with open(file_path, 'r') as file:
            for line in file:
                if match in line: return line
    else:
        with FileReadBackwards(file_path) as file:
            for i in range(lines):
                line = file.readline()
                if 'banlist' in match:
                    if 'was banned by' in line:  # finds log lines that shows banned players.
                        log_data += line
                    elif ']: There are' in line:  # finds the end so it doesn't return everything from log other then banned users.
                        log_data += line
                        break

                elif log_mode:
                    log_data += line
                elif match in line:
                    log_data = line
                    break

    if return_bool and not log_data:
        return False

    if log_data:
        return log_data
    else: return False

# Gets server stats from mctools PINGClient. Returned dictionary data contains ansi escape chars.
def mc_ping():
    """
    Gets server information using mctools.PINGClient()

    Returns:
        dict: Dictionary containing 'version', and 'description' (motd).

    """
    try: stats = mctools.PINGClient(mc_ip).get_stats()
    except ConnectionRefusedError:
        lprint("Ping Error: Connection Refused.")
    else: return stats

# Get server active status, motd, and version information. Either using PINGClient or reading from local server files.
async def mc_status():
    """
    Gets server active status, by sending command to server and checking server log.

    Returns:
        bool: Server active status.
    """

    status = await mc_command('STATUS ' + str(random.random()), return_bool=True)
    if status:
        server_active_status = True
    else: server_active_status = False
    return server_active_status

def get_mc_motd():
    """
    Gets current message of the day from server, either by reading from server.properties file or using PINGClient.

    Returns:
        str: Server motd.
    """

    if server_files_access:
        return edit_properties('motd')[1]
    elif use_rcon:
        return remove_ansi(mc_ping()['description'])
    else: return "N/A"

# Gets server version from log file or gets latest version number from website.
def mc_version():
    """
    Gets server version, either by reading server log or using PINGClient.

    Returns:
        str: Server version number.
    """

    if use_rcon:
        return mc_ping()['version']['name']
    elif server_files_access:
        if version := mc_log('server version', normal_read=True):
            version = version.split()[-1]
            with open(f"{server_path}/version.txt", 'w') as f: f.write(version)
            return version
        else:
            with open(f"{server_path}/version.txt", 'r') as f: return f.readline()
    return 'N/A'

def get_latest_version():
    """
    Gets latest Minecraft server version number from official website using bs4.

    Returns:
        str: Latest version number.
    """

    soup = BeautifulSoup(requests.get(new_server_url).text, 'html.parser')
    for i in soup.findAll('a'):
        if i.string and 'minecraft_server' in i.string:
            return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.

# Used so Discord command arguments don't need qoutes.
def format_args(args, return_empty=False):
    """
    Formats passed in *args from Discord command functions.
    This is so quotes aren't necessary for Discord command arguments.

    Args:
        args: Passed in args to combine and return.
        return_empty: returns empty str if passed in arguments aren't usable for Discord command.

    Returns:
        str: Arguments combines with spaces.
    """

    if args: return ' '.join(args)
    else:
        if return_empty: return ''
        return "No reason given"

# Gets data from json local file.
def get_json(json_file):
    os.chdir(server_functions_path)
    with open(server_path + '/' + json_file) as file:
        return [i for i in json.load(file)]

def get_csv(csv_file):
    os.chdir(server_functions_path)
    with open(csv_file) as file:
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

# ========== Extra server functions.
def download_new_server():
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

    if not jar_download_url: return

    # Saves new server.jar in current server.
    version = requests.get(jar_download_url).content
    with open(server_path + '/server.jar', 'wb') as jar_file:
        jar_file.write(version)

    # Updates eula.txt to true.
    with open(server_path + '/eula.txt', 'w') as file: file.write('eula=true')

    return version

# Reads, find, or replace properties in a .properties file, edits inplace using fileinput.
def edit_properties(target_property=None, value='', file_path=f"{server_path}/server.properties"):
    """
    Edits server.properties file if received target_property and value.
    If receive no value, will return current set value if property exists.

    Args:
        target_property: Find Minecraft server property.
        value: If received argument, will change value.
        file_path: File to edit. Must be in .properties file format. Default is server.properties file under /server folder containing server.jar.

    Returns:
        str: If target_property was not found.
        tuple: First item is line from file that matched target_property. Second item is just the current value.
    """

    os.chdir(server_path)
    return_line = discord_return = ''
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)
            if target_property == 'all':
                discord_return += F"`{line.rstrip()}`\n"
                return_line += line.strip() + '\n'
                print(line, end='')
            elif target_property in split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value
                    new_line = '='.join(split_line)
                    discord_return = f"Updated Property:`{line}` > `{new_line}`.\nRestart to apply changes."
                    return_line = line
                    print(new_line, end='\n')
                else:
                    discord_return = f"`{'='.join(split_line)}`"
                    return_line = '='.join(split_line)
                    print(line, end='')
            else: print(line, end='')

    if return_line:  # If property not found.
        return return_line, return_line.split('=')[1]
    else: return "404: Property not found!"

# Get server or world backup folder name from index.
def get_from_index(path, index): return os.listdir(path)[index]

# Gets x number of backups.
def fetch_backups(path, amount=5):
    backups = []
    for item in os.listdir(path)[:amount]:
        if os.path.isdir(path + '/' + item):
            backups.append(item)
    return backups

def create_backup(name, src, dst):
    if not os.path.isdir(dst): os.makedirs(dst)

    folder_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
    new_name = f"({folder_timestamp}) {mc_version()} {name}"
    new_backup_path = dst + '/' + new_name
    shutil.copytree(src, new_backup_path)

    if os.path.isdir(new_backup_path):
        lprint("Backed up to: " + new_backup_path)
        return new_name
    else:
        lprint("Error creating backup at: " + new_backup_path)
        return False

def restore_backup(backup, dst, reset=False):
    try: shutil.rmtree(dst)
    except: pass

    # This function is used in ?rebirth Discord command to create a new world.
    if reset: return True

    try:
        shutil.copytree(backup, dst)
        return True
    except: lprint("Error restoring: " + str(backup + ' > ' + dst))

def delete_backup(backup):
    try:
        shutil.rmtree(backup)
        return True
    except: lprint("Error deleting: " + str(backup))


# ========== Discord commands.
def get_server_from_index(index): return get_from_index(server_backups_path, index)
def get_world_from_index(index): return get_from_index(world_backups_path, index)

def fetch_servers(amount=5): return fetch_backups(server_backups_path, amount)
def fetch_worlds(amount=5): return fetch_backups(world_backups_path, amount)

def backup_server(name='server_backup'): return create_backup(name, server_path, server_backups_path)
def backup_world(name="world_backup"): return create_backup(name, server_path + '/world', world_backups_path)

def delete_server(server): return delete_backup(server_backups_path + '/' + server)
def delete_world(world): return delete_backup(world_backups_path + '/' + world)

def restore_server(server=None, reset=False):
    os.chdir(server_backups_path)
    return restore_backup(server, server_path, reset)
def restore_world(world=None, reset=False):
    os.chdir(world_backups_path)
    return restore_backup(world, server_path + '/world', reset)
