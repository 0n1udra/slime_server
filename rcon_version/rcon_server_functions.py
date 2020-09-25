import os, datetime, mctools

server_functions_path = os.getcwd()

# RCON
mc_rcon_ip = 'arcpy.asuscomm.com'
mc_rcon_port = 25575
mc_rcon_pass_file = "/home/slime/mc_rcon_pass.txt"

# Updates variables as needed.
discord_bot_token_file = '/home/slime/mc_bot_token.txt'
discord_bot_file = f"{server_functions_path}/discord_mc_bot.py"
discord_bot_log_file = f"{server_functions_path}/bot_log.txt"
rcon_command_info_file = f"rcon_command_info.csv"

# Special print function that logs also.
def lprint(arg1=None, arg2=None):
    if type(arg1) is str:
        msg = arg1
        user = 'Script'
    else:
        try:
            user = arg1.message.author
        except: user = 'N/A'
        msg = arg2

    output = f"{datetime.datetime.now()} | ({user}) {msg}"

    with open(discord_bot_log_file, 'a') as file:
        file.write(output + '\n')

    print(output)

def mc_rcon(command=''):
    if os.path.isfile(mc_rcon_pass_file):
        with open(mc_rcon_pass_file, 'r') as file:
            mc_rcon_pass = file.readline().strip()
    else:
        print("Error finding RCON password file.")
        return

    mc_rcon_client = mctools.RCONClient(mc_rcon_ip, port=mc_rcon_port)

    if mc_rcon_client.login(mc_rcon_pass):
        response = mc_rcon_client.command(command)
        return response
    else: print("Error connecting RCON.")

def setup_directories():
    try:
        os.makedirs(server_path)
        os.makedirs(world_backups_path)
        os.makedirs(server_backups_path)
    except: print("Error: Something went wrong setup up necessary directory structure.")

# Gets server version from file or from website.
def get_minecraft_version(get_latest=False):
    pass


if __name__ == '__main__':
    pass

