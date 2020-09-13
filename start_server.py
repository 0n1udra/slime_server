import os, sys, time, shutil
from os.path import join

java_path = '/mnt/c/Program Files/Java/jre1.8.0_261/bin/java.exe'
server_path = '/mnt/c/Users/DT/Desktop/MC/server'
server_jar = f'{server_path}/server.jar'
start_tmux = 'tmux new -d -s mcserver'
run_args = f'java -Xmx2G -Xms1G -jar {server_jar} nogui java'
start_server_command = f'tmux send-keys -t mcserver.0 "{run_args}" ENTER'

process = None

def server_command(cmd):
    process.stdin.write(f'{cmd}\n')

def start_server():
    os.chdir(server_path)
    os.system(start_tmux)
    os.system(start_server_command)

start_server()
