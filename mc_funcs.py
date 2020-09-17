from bs4 import BeautifulSoup
import os, shutil, datetime, fileinput, urllib, re


def lprint(msg): print(f"{datetime.datetime.now()} | {msg}")

new_server_url = 'https://www.minecraft.net/en-us/download/server'

file_path = os.getcwd()
mc_path = '/mnt/c/Users/DT/Desktop/MC'
server_path = f"{mc_path}/server"
backups_path = f"{mc_path}/backups"
server_jar_path = f'{server_path}/server.jar'
properties_file = f"{server_path}/server.properties"

new_bot = "tmux send-keys -t mcserver:2.2 {bot_file_path} ENTER"
new_tmux = 'tmux new -d -s mcserver'
java_args = f'java -Xmx2G -Xms1G -jar {server_jar_path} nogui java'
start_server_command = f'tmux send-keys -t mcserver:1.0 "{java_args}" ENTER'
popen_commands = ['java', '-Xmx2G', '-Xms1G', '-jar', server_jar_path, 'nogui', 'java']


def start_server():
    os.chdir(server_path)
    # Tries starting new detached tmux session.
    try: os.system(new_tmux)
    except: lprint("Error starting detached tmux session with name: mcserver")
    if not os.system(start_server_command): return True

def backup_world(name='backup', mc_version='1.16.3'):
    os.chdir(server_path)
    if not os.path.isdir(backups_path): os.mkdir(backups_path)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
    new_backup = f"({timestamp}) {mc_version} {name}"
    new_backup_path = backups_path + '/' + new_backup
    shutil.copytree(server_path + '/world', new_backup_path)

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
        yield f"{index})", world

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
    except:
        lprint("Error restoring: " + str(world))
    

def delete_world(world):
    os.chdir(backups_path)
    try: shutil.rmtree(world)
    except: 
        lprint("Error deleting current world folder at: " + str(backups_path))
        return False

def edit_properties(target_property=None, value=''):
    os.chdir(file_path)
    return_line = ''
    with fileinput.FileInput(properties_file, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)
            if target_property == 'all':
                return_line += F"`{line.rstrip()}`\n"
                print(line, end='')
            elif target_property == split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value
                    new_line = '='.join(split_line)
                    return_line = f"**Updated Property:** `{line}` > `{new_line}`.\nRestart to apply changes."
                    print(new_line, end='')
                else:
                    return_line = f"`{'='.join(split_line)}`"
                    print(line, end='')
            else: print(line, end='')

    # Sends Discord message saying property not found.
    if return_line:
        return return_line
    else: return "**404:** Property not found!"

def download_new_server():
    html_page = urllib.request.urlopen(new_server_url)
    soup = BeautifulSoup(html_page)
    links = []

    for link in soup.findAll('a', attrs={'href': re.compile("^http://")}): links.append(link.get('href'))

    return links


if __name__ == '__main__':
    print(edit_properties('all'))
    pass
