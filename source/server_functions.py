import os, datetime, csv, time
from file_read_backwards import FileReadBackwards
from bs4 import BeautifulSoup

server_functions_path = os.getcwd()
bot_log_file = f"{server_functions_path}/bot_log.txt"

# Outputs and logs used bot commands and which Discord user invoked them.
def lprint(arg1=None, arg2=None):
    if type(arg1) is str:
        msg = arg1
        user = 'Script'
    else:
        try: user = arg1.message.author
        except: user = 'N/A'
        msg = arg2

    output = f"{datetime.datetime.now()} | ({user}) {msg}"
    print(output)

    with open(bot_log_file, 'a') as file:
        file.write(output + '\n')

# If you have local access to server files but not using Tmux, use RCON to send commands to server. You won't be able to use some features like server logging.
use_rcon = False
mc_ip = 'arcpy.asuscomm.com'
rcon_port = 25575
rcon_pass = 'SlimeySlime'
lprint(f"RCON Enabled: {mc_ip} : {rcon_port}")

# Local file access allows for server files/folders manipulation for features like backup/restore world saves or editing server.properties file.
server_files_access = True
# This is where Minecraft server, world backups and some Discord bot files will be saved, so make sure this is an absolute path and is where you want it.
# The setup_directories() function when running 'run_bot.py setup' uses os.makedirs(), which will recursively make subdirectories if they don't exists already. Read more: https://www.tutorialspoint.com/python/os_makedirs.htm
# os.makedirs() will not overwrite existing files/folders.
minecraft_folder_path = '/mnt/c/Users/DT/Desktop/MC'
lprint("Minecraft directory: " + minecraft_folder_path)

server_path = f"{minecraft_folder_path}/server"
world_backups_path = f"{minecraft_folder_path}/world_backups"
server_backups_path = f"{minecraft_folder_path}/server_backups"
server_jar_file = f'{server_path}/server.jar'
server_log_file = f"{server_path}/output.txt"
server_properties_file = f"{server_path}/server.properties"
bot_file = f"{server_functions_path}/discord_mc_bot.py"
bot_properties_file = f"{server_path}/discord-bot.properties"
bot_token_file = '/home/slime/mc_bot_token.txt'
script_properties_file = f'{server_functions_path}/script_properties.txt'

# Update server.jar execution argument if needed.
java_args = f'java -Xmx2G -Xms1G -jar {server_jar_file} nogui java 2>&1 | tee -a output.txt'
lprint("Java run command set: " + java_args)

# Use Tmux to send commands to server and log server output to file. You can disable Tmux and RCON to disable server control, and can just use files/folder manipulation features.
use_tmux = True
start_server_command = f'tmux send-keys -t mcserver:1.0 "{java_args}" ENTER'
lprint("Tmux send server command set: " + start_server_command)

folder_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
new_server_url = 'https://www.minecraft.net/en-us/download/server'

if use_rcon: import mctools, re
if server_files_access: import shutil, requests, fileinput, json

# Sends command to tmux window running server.
def mc_command(command, match_output=None):
    if use_rcon: return mc_rcon(command)

    os.system(f'tmux send-keys -t mcserver:1.0 "/{command}" ENTER')
    time.sleep(1)
    if match_output is None:
        return get_output(command)
    else: return get_output(match_output)

def mc_rcon(command=''):
    mc_rcon_client = mctools.RCONClient(mc_ip, port=rcon_port)

    if mc_rcon_client.login(rcon_pass):
        response = mc_rcon_client.command(command)
        return response
    else: lprint("Error connecting RCON.")

# Removes unwanted ANSI escape characters.
def remove_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Gets server stats from mctools PINGClient. Returned dictionary data contains ansi escape chars.
def mc_ping_stats():
    stats = mctools.PINGClient(mc_ip).get_stats()
    stats = {'motd': remove_ansi(stats['description']),
             'version': stats['version']['name']}
    return stats

# Get server active status, motd, and version information. Either using PINGClient or reading from local server files.
def get_server_status():
    if 'testcheckstring' not in mc_command('testcheckstring'): return False

    if use_rcon:
        return mc_ping_stats()
    else:
        return {'motd': edit_properties('motd')[2][:-1],
                'version': get_minecraft_version()}

# Used so Discord command arguments don't need qoutes.
def format_args(args, return_empty=False):
    if args: return ' '.join(args)
    else:
        if return_empty:
            return ''
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


def start_discord_bot():
    os.system(f'tmux send-keys -t mcserver:1.1 "cd {server_functions_path}" ENTER')
    if not os.system("tmux send-keys -t mcserver:1.1 'python3 discord_mc_bot.py' ENTER"): return True


# Starts minecraft server in Tmux session.
def start_minecraft_server():
    # Fix: 'java.lang.Error: Properties init: Could not determine current working' error
    os.system('tmux send-keys -t mcserver:1.0 "cd /" ENTER')
    os.system(f'tmux send-keys -t mcserver:1.0 "cd {server_path}" ENTER')

    # Tries starting new detached tmux session.
    if not os.system(start_server_command): return True

# Gets server output by reading log file, can also find response from command in log by finding matching string.
def get_output(match='placeholder match', file_path=server_log_file, lines=50):
    log_data = match_found = ''
    with FileReadBackwards(file_path) as file:
        for i in range(lines):
            line = file.readline()
            if 'banlist' in match:
                # Finds log lines that shows banned players.
                if 'was banned by' in line:
                    match_found += line
                # Finds the end so it doesn't return everything from log other then banned users.
                elif '/INFO]: There are' in line:
                    match_found += line
                    break

            elif match in line:
                match_found = line
                break
            log_data += line

    if match_found:
        return match_found
    return log_data

# Get server or world backup folder name from index.
def get_from_index(path, index):
    return os.listdir(path)[index]

# Gets x number of backups.
def fetch_backups(path, amount=5):
    backups = []
    for item in os.listdir(path)[:amount]:
        if os.path.isdir(path + '/' + item):
            backups.append(item)
    return backups

def create_backup(name, src, dst):
    if not os.path.isdir(dst):
        os.makedirs(dst)

    new_name = f"({folder_timestamp}) {get_minecraft_version()} {name}"
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
    except: 
        lprint("Error deleting: " + dst)
        return False

    # This function is used in ?rebirth Discord command to create a new world.
    if reset: return True

    try: 
        shutil.copytree(backup, server_path + dst)
    except: lprint("Error restoring: " + str(backup))
    
def delete_backup(backup):
    try:
        shutil.rmtree(backup)
        return True
    except: lprint("Error deleting: " + str(backup))

# Downloads latest server.jar from Minecraft website in current server folder, also updates needed files like eula.txt.
def download_new_server():
    os.chdir(minecraft_folder_path)
    jar_download_url = ''

    minecraft_website = requests.get(new_server_url)
    soup = BeautifulSoup(minecraft_website.text, 'html.parser')
    # Finds Minecraft server.jar urls in div class.
    div_agenda = soup.find_all('div', class_='minecraft-version')
    for i in div_agenda[0].find_all('a'):
        jar_download_url = f"{i.get('href')}"

    if not jar_download_url: return

    mc_ver = get_minecraft_version(get_latest=True)
    # Saves new server.jar in current server.
    with open(server_path + '/server.jar', 'wb') as jar_file:
        jar_file.write(requests.get(jar_download_url).content)

    # Updates server discord-bot.properties file. server.properties will remove foreign data on server start.
    if not os.path.isfile(bot_properties_file):
        with open(bot_properties_file, 'w+') as file:
            file.write('version=' + mc_ver)
    else:
        edit_properties('version', )
        with fileinput.FileInput(bot_properties_file, inplace=True) as file:
            for line in file:
                if file.isfirstline():
                    print('version=' + mc_ver, end='\n')
                else: print(line, end='')

    with open(server_path + '/eula.txt', 'w') as file:
        file.write('eula=true')

    return mc_ver

# Gets server version from file or gets latest version number from website.
def get_minecraft_version(get_latest=False):
    # Returns server version from Discord-server.properties file located in same folder as server.jar.
    if not get_latest: return edit_properties('version', file_path=bot_properties_file)[2]

    soup = BeautifulSoup(requests.get(new_server_url).text, 'html.parser')
    for i in soup.findAll('a'):
        # Returns Minecraft server version by splitting up string and extracting only numbers then recombining.
        if i.string and 'minecraft_server' in i.string:
            return '.'.join(i.string.split('.')[1:][:-1])

# Reads, find, or replace properties in a .properties file, edits inplace using fileinput.
# Return values: name=value, `name=value`, value
def edit_properties(target_property=None, value='', file_path=server_properties_file):
    os.chdir(server_path)
    # Return data for other script uses, and one specifically for Discord.
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

    # Sends Discord message saying property not found.
    if return_line:
        return return_line, discord_return, return_line.split('=')[1]
    else: return return_line, "404: Property not found!"

# Functions for discord bot.
def get_server_from_index(index): return get_from_index(server_backups_path, index)
def get_world_from_index(index): return get_from_index(world_backups_path, index)

def fetch_servers(amount=5): return fetch_backups(server_backups_path, amount)
def fetch_worlds(amount=5): return fetch_backups(world_backups_path, amount)

def backup_server(name='server_backup'): return create_backup(name, server_path, server_backups_path)
def backup_world(name="world_backup"): return create_backup(name, server_path + '/world', world_backups_path)

def restore_server(server=None, reset=False): return restore_backup(server, server_path, reset)
def restore_world(world=None, reset=False): return restore_backup(world, server_path + '/world', reset)

def delete_server(server): return delete_backup(server_backups_path + '/' + server)
def delete_world(world): return delete_backup(world_backups_path + '/' + world)
