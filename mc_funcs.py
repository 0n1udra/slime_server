from bs4 import BeautifulSoup
import os, shutil, datetime, fileinput, urllib, re, requests


def lprint(msg): print(f"{datetime.datetime.now()} | {msg}")

folder_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
new_server_url = 'https://www.minecraft.net/en-us/download/server'

file_path = os.getcwd()
mc_path = '/mnt/c/Users/DT/Desktop/MC'
server_path = f"{mc_path}/server"
backups_path = f"{mc_path}/world_backups"
server_jar_path = f'{server_path}/server.jar'
server_backups_path = f"{mc_path}/server_backups"
properties_file = f"{server_path}/server.properties"
version_file = f"{server_path}/version.txt"

new_bot = "tmux send-keys -t mcserver:2.2 {bot_file_path} ENTER"
new_tmux = 'tmux new -d -s mcserver'
java_args = f'java -Xmx2G -Xms1G -jar {server_jar_path} nogui java'
start_server_command = f'tmux send-keys -t mcserver:1.0 "{java_args}" ENTER'
popen_commands = ['java', '-Xmx2G', '-Xms1G', '-jar', server_jar_path, 'nogui', 'java']


def start_server():
    # Fix: 'java.lang.Error: Properties init: Could not determine current working' error
    os.system('tmux send-keys -t mcserver:1.0 "cd /" ENTER')
    os.system(f'tmux send-keys -t mcserver:1.0 "cd {server_path}" ENTER')

    os.chdir(server_path)

    # Tries starting new detached tmux session.
    try: os.system(new_tmux)
    except: lprint("Error starting detached tmux session with name: mcserver")
    if not os.system(start_server_command): return True

# ========== World Saves.
def backup_world(name='backup'):
    os.chdir(server_path)
    if not os.path.isdir(backups_path): os.mkdir(backups_path)

    new_backup = f"({folder_timestamp}) {get_minecraft_version()} {name}"
    new_backup_path = backups_path + '/' + new_backup
    shutil.copytree(server_path + '/world', backups_path + '/' + new_backup)

    if os.path.isdir(new_backup_path):
        lprint("Backed up to: " + new_backup_path)
        return new_backup
    else: 
        lprint("Error backing up world folder to: " + new_backup_path)
        return False

def fetch_worlds(amount=5):
    # Yields index and world folder name.
    os.chdir(backups_path)
    for index, world in enumerate(os.listdir(backups_path)[:amount]):
        if os.path.isdir(world): yield f"{index})", world

def get_world_from_index(index):
    os.chdir(backups_path)
    return os.listdir(backups_path)[index]

def restore_world(world=None, reset=False):
    os.chdir(backups_path)

    try: shutil.rmtree(server_path + '/world')
    except: 
        lprint("Error deleting current world folder at: " + server_path)
        return False

    # This function is used in ?rebirth discord command to create a new world.
    if reset: return True

    try: shutil.copytree(world, server_path + '/world')
    except: lprint("Error restoring: " + str(world))
    
def delete_world(world):
    os.chdir(backups_path)
    try:
        shutil.rmtree(world)
        return True
    except: lprint("Error deleting current world folder at: " + str(backups_path))


# ========== Server Backups.
def get_minecraft_version(get_latest=False):
    if not get_latest:
        with open(version_file, 'r') as f: return f.readline()

    soup = BeautifulSoup(requests.get(new_server_url).text, 'html.parser')
    for i in soup.findAll('a'):
        # Returns Minecraft server version by splitting up string and extracting only numbers then recombining.
        if i.string and 'minecraft_server' in i.string:
            return '.'.join(i.string.split('.')[1:][:-1])

def download_new_server():
    os.chdir(mc_path)
    jar_download_url = ''

    minecraft_website = requests.get(new_server_url)
    soup = BeautifulSoup(minecraft_website.text, 'html.parser')
    # Finds Minecraft server.jar urls in div class.
    div_agenda = soup.find_all('div', class_='minecraft-version')
    for i in div_agenda[0].find_all('a'): jar_download_url = f"{i.get('href')}"

    # Downloads new server jar if found url.
    if jar_download_url:
        mc_ver = get_minecraft_version(get_latest=True)
        with open(server_path + '/server.jar', 'wb') as jar_file: jar_file.write(requests.get(jar_download_url).content)
        # Updates server version.txt. Using seperate file because server.properties will remove foreign data on server start.
        with open(version_file, 'w') as f: f.write(mc_ver)
        return mc_ver

def fetch_servers(amount=5):
    # Yields index and world folder name.
    os.chdir(server_backups_path)
    for index, server in enumerate(os.listdir(server_backups_path)[:amount]):
        if os.path.isdir(server): yield f"{index})", server

def get_server_from_index(index):
    os.chdir(server_backups_path)
    return os.listdir(server_backups_path)[index]

def backup_server(name='backup'):
    os.chdir(mc_path)
    if not os.path.isdir(server_backups_path): os.mkdir(server_backups_path)

    new_backup = f"({folder_timestamp}) {get_minecraft_version()} {name}"
    new_backup_path = backups_path + '/' + new_backup
    shutil.copytree(server_path, server_backups_path + '/' + new_backup)

    if os.path.isdir(new_backup_path):
        lprint("Server backup saved to: " + new_backup_path)
        return new_backup
    else:
        lprint("Error backing up server to: " + new_backup_path)
        return False

def restore_server(server=None, reset=False):
    os.chdir(server_backups_path)

    # Sets up eula so server can start.
    if reset:
        os.mkdir(mc_path + '/server/')
        download_new_server()
        with open(server_path + '/eula.txt', 'w') as f: f.write("eula=true")

    if server:
        try:
            os.system(f'cd "{server_path}" && cp -r "{server_backups_path}/{server}"/* ./')
            return True
        except: return False

def delete_server(server):
    os.chdir(server_backups_path)
    try:
        shutil.rmtree(server)
        return True
    except: lprint("Error deleting server at: " + str(server_backups_path))


def edit_properties(target_property=None, value=''):
    os.chdir(file_path)
    return_line = ''
    with fileinput.FileInput(properties_file, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)
            # Get server version, need this line because
            if target_property == 'all':
                return_line += F"`{line.rstrip()}`\n"
                print(line, end='')
            elif target_property in split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value
                    new_line = '='.join(split_line)
                    return_line = f"**Updated Property:** `{line}` > `{new_line}`.\nRestart to apply changes."
                    print(new_line, end='\n')
                else:
                    return_line = f"`{'='.join(split_line)}`"
                    print(line, end='')
            else: print(line, end='')

    # Sends Discord message saying property not found.
    if return_line:
        return return_line
    else: return "**404:** Property not found!"

if __name__ == '__main__':
    #print(edit_properties('all'))
    #download_new_server()
    restore_server(get_server_from_index(0))
    pass
