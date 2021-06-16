import datetime, requests, csv, os, re
from slime_vars import *

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
        args: Passed in args to combine and return.
        return_empty (bool False): returns empty str if passed in arguments aren't usable for Discord command.

    Returns:
        str: Arguments combines with spaces.
    """

    if args:
        return ' '.join(args)
    else:
        if return_empty_str is True:
            return ''
        return "No reason given."

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
