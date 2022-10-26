import subprocess, fileinput, requests, datetime, shutil, psutil, json, math, csv, os, re
import slime_vars
import bot_files.components as components

ctx = 'backend.py'
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

def get_parameter(arg, nrg_msg=False, key='second_selected', **kwargs):
    """
    Gets needed parameter for function to run properly.
    Discord commands can be called from buttons or prefix command.
    If using prefix command, it'll just format the parameters as needed.
    If function being called from button, will get needed parameter using components.data func.

    Args:
        arg: Will either receive parameters from using prefix, or will be bmode.
        nrg_msg bool: Returns 'No reason given' string, if arg is empty.
        key str: Key of data dict to get parameter from. Used for getting selection from components.
    """

    # Checks if command was called from button
    if 'bmode' in arg:
        from_data_dict = components.data(key, reset=True)
        if from_data_dict: return from_data_dict

    elif type(arg) in (list, tuple):
        return ' '.join(arg)

    if not arg: return ''
    if nrg_msg and not arg: return "No reason given."

    return arg

def group_items(items, size=25):
    """
    Discord select componenet can only show 25 items at a time.
    This is to group items in sublist of 25.

    Args:
        items list: list of items to subgroup.
        size int: Size of sublist.
    """

    try:
        grouped_list = [items[i:i + size] for i in range(0, len(items), size)]
        num_of_groups = math.ceil(len(items) / size)
        return grouped_list, num_of_groups
    except: return None, None

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

# ========== File/folder editing/manipulation
def edit_file(target_property=None, value='', file_path=f"{slime_vars.server_path}/server.properties"):
    """
    Edits server.properties file if received target_property and value. Edits inplace with fileinput
    If receive no value, will return current set value if property exists.

    Args:
        target_property str(None): Find Minecraft server property.
        value str(''): If received argument, will change value.
        file_path str(server.properties): File to edit. Must be in .properties file format. Default is server.properties file under /server folder containing server.jar.

    Returns:
        str: If target_property was not found.
        tuple: First item is line from file that matched target_property. Second item is just the current value.
    """

    try: os.chdir(slime_vars.server_path)
    except: pass
    return_line = ''

    # print() writes to file while using it in FileInput() with inplace=True
    # fileinput doc: https://docs.python.org/3/library/fileinput.html
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)

            if target_property == 'all':  # Return all lines of file.
                return_line += line.strip() + '\n'
                print(line, end='')

            # If found match, and user passed in new value to update it.
            elif target_property in split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value  # edits value section of line
                    new_line = return_line = '='.join(split_line)
                    print(new_line, end='\n')  # Writes new line to file
                # If user did not pass a new value to update property, just return the line from file.
                else:
                    return_line = '='.join(split_line)
                    print(line, end='')
            else: print(line, end='')

    if return_line:
        return return_line, return_line.split('=')[1].strip()
    else: return "Match not found.", 'Match not found.'

def read_json(json_file):
    """Read .json files."""
    with open(json_file) as file:
        return [i for i in json.load(file)]

def read_csv(csv_file):
    """Read .csv files in bot_files directory."""
    os.chdir(slime_vars.bot_files_path)
    with open(csv_file) as file:
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

def update_csv(csv_file, new_data=None):
    """Updates csv files in bot_files directory."""

    os.chdir(slime_vars.bot_files_path)

    with open(csv_file, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(new_data)

def update_servers(new_data=None):
    if new_data:
        slime_vars.servers[new_data['name']] = [new_data['name'], new_data['description'], new_data['command'], new_data['wait']]

    update_csv('servers.csv', [i for i in slime_vars.servers.values()])

def get_from_index(path, index, mode):
    """
    Get server or world backup folder name from passed in index number

    Args:
        path str: Location to find world or server backups.
        index int: Select specific folder, get index from other functions like ?worldbackupslist, ?serverbackupslist

    Returns:
            str: file path of selected folder.
    """

    items = ['placeholder']  # Listed items in Discord (select menus, embeds) start at 1 (for user convients). But python is 0, soooo, yeah. need this.
    for i in reversed(sorted(os.listdir(path))):
        if mode == 'f': items.append(i)
        elif mode == 'd': items.append(i)
        else: continue

    return f'{path}/{items[index]}'

def enum_dir(path, mode, index_mode=False):
    """
    Returns enumerated list of directories in path.

    Args:
        path str: Path of world or server backups location.
        mode str: Aggregate only files or only directories.
        index_mode bool: Put index as second item in list.
    """

    return_list = []
    if not os.path.isdir(path): return False

    index = 1
    for item in reversed(sorted(os.listdir(path))):
        # Appends only either file or directory to items list.
        flag = False
        if 'f' in mode:
            if os.path.isfile(os.path.join(path, item)): flag = True
        elif 'd' in mode:
            if os.path.isdir(os.path.join(path, item)): flag = True

        if flag:
            index += 1
            if index_mode:
                return_list.append([item, index, False, index])  # Need this for world/server commands
                continue
            if 's' in mode and item in slime_vars.servers:
                return_list.append([item, item, False, slime_vars.servers[item][1]])  # For server mode for ?controlpanel command component
                continue
            return_list.append([item, item, False, index])  # Last 2 list items is for new_selection.
        else: continue
    return return_list

def delete_dir(backup):
    """
    Delete world or server backup.

    Args:
        backup str: Path of backup to delete.
    """

    shutil.rmtree(backup)

