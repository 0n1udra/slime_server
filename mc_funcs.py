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
    if os.system(new_tmux):
        lprint("Error starting detached tmux session with name: mcserver")
        return False

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
    os.chdir(backups_path)
    for index, world in enumerate(os.listdir(backups_path)[:amount]):
        yield f"{index})", world

def restore_world(index):
    pass


if __name__ == '__main__':
    pass
    #backup_world(
    #star_server()
