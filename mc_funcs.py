#from bs4 import BeautifulSoup
import shutil as su
import os, shutil, asyncio, datetime
from subprocess import Popen, PIPE

def lprint(msg): print(f"{datetime.datetime.now()} | {msg}")


file_path = os.path.dirname(__file__)
mc_path = '/mnt/c/Users/DT/Desktop/MC'
server_path = f"{mc_path}/server"
backups_path = f"{mc_path}/backups"

server_jar = f'{server_path}/server.jar'
new_tmux = 'tmux new -d -s mcserver'
java_args = f'java -Xmx2G -Xms1G -jar {server_jar} nogui java'
start_server_command = f'tmux send-keys -t mcserver:1.0 "{java_args}" ENTER'
popen_commands = ['java', '-Xmx2G', '-Xms1G', '-jar', server_jar, 'nogui', 'java']


def start_server():
    os.chdir(server_path)
    try: os.system(new_tmux)
    except:
        lprint("Error starting detached tmux session with name: mcserver")

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


if __name__ == '__main__':
    pass
    print(get_world_from_index(2))
    #backup_world(
    #restore_world(0)

