import subprocess, requests, datetime, psutil, json, math, csv, os, re
from bs4 import BeautifulSoup
import slime_vars

ctx = 'backend_functions.py'
enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']

def lprint(ctx, msg):
    """Prints and Logs events in file."""
    try:
        user = ctx.message.author
    except:
        user = ctx

    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({user}): {msg}"
    print(output)

    # Logs output.
    with open(slime_vars.bot_log_file, 'a') as file:
        file.write(output + '\n')

lprint(ctx, "Server selected: " + slime_vars.server_selected[0])

def group_items(items, size=25):
    """
    Discord select componenet can only show 25 items at a time.
    This is to group items in sublist of 25.

    Args:
        items list: list of items to subgroup.
        size int: Size of sublist.
    """

    grouped_list = [items[i:i + size] for i in range(0, len(items), size)]
    num_of_groups = math.ceil(len(items) / size)
    return grouped_list, num_of_groups

def get_proc(proc_name, proc_cmdline=None):
    """Returns a process by matching name and argument."""

    for proc in psutil.process_iter():
        if proc.name() == proc_name:
            # Narrow down process by it's arguments. E.g. python3 could have multiple processes.
            if proc_cmdline:
                if any(proc_cmdline in i for i in proc.cmdline()):
                    return proc
            else:
                return proc

def format_args(args, return_no_reason=False):
    """
    Formats passed in *args from Discord command functions.
    This is so quotes aren't necessary for Discord command arguments.

    Args:
        args str: Passed in args to combine and return.
        return_no_reason bool(False): returns string 'No reason given.' for commands that require a reason (kick, ban, etc).

    Returns:
        str: Arguments combines with spaces.
    """

    if args: return ' '.join(args)
    else:
        if return_no_reason is True:
            return "No reason given."
        return ''

def format_coords(coordinates):
    pass

def get_datetime():
    """Returns date and time. (2021-12-04 01-49)"""

    return datetime.datetime.now().strftime('%Y-%m-%d %H-%M')

def remove_ansi(text):
    """Removes ANSI escape characters."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def read_json(json_file):
    """Read .json files."""
    os.chdir(slime_vars.bot_files_path)
    with open(slime_vars.server_path + '/' + json_file) as file:
        return [i for i in json.load(file)]

def read_csv(csv_file):
    """Read .csv files."""
    os.chdir(slime_vars.bot_files_path)
    with open(csv_file) as file:
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

def get_public_ip():
    """Gets your public IP address, to updates server ip address varable using request.get()"""

    global server_ip
    try:
        server_ip = json.loads(requests.get('http://jsonip.com').text)['ip']
        slime_vars.server_ip = server_ip
    except: return None
    return server_ip

def ping_url():
    """Checks if server_url address works by pinging it twice."""

    ping = subprocess.Popen(['ping', '-c', '2', slime_vars.server_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ping_out, ping_error = ping.communicate()
    if slime_vars.server_ip in str(ping_out):
        return 'working'
    return 'inactive'
