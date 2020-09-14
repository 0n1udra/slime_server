import os

# A simple script that starts minecraft java server in a detached tmux session

server_path = '/mnt/c/Users/DT/Desktop/MC/server'
server_jar = f'{server_path}/server.jar'
start_new_tmux = 'tmux new -d -s mcserver'
run_args = f'java -Xmx2G -Xms1G -jar {server_jar} nogui java'
start_server_command = f'tmux send-keys -t mcserver:1.0 "{run_args}" ENTER'

def start_server():
    os.chdir(server_path)
    #tmux_status = os.system(start_tmux)
    if not os.system(start_server_command):
        return True


if __name__ == '__main__':
    start_server()
