import subprocess, fileinput, requests, datetime, shutil, psutil, json, math, csv, os, re, io
import bot_files.slime_vars as slime_vars
import bot_files.components as components

ctx = 'extra.py'
enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']
slime_proc = slime_pid = None  # If using nohup to run bot in background.
slime_proc_name, slime_proc_cmdline = 'python3',  'slime_bot.py'  # Needed to find correct process if multiple python process exists.

def lprint(ctx, msg):
    """Prints and Logs events in file."""
    try: user = ctx.message.author
    except: user = ctx

    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({user}): {msg}"
    print(output)

    # Logs output.
    with open(slime_vars.bot_log_filepath, 'a') as file:
        file.write(output + '\n')

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
            # Narrow down process by its arguments. E.g. python3 could have multiple processes.
            if proc_cmdline:
                if any(proc_cmdline in i for i in proc.cmdline()):
                    return proc
            else: return proc

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

def ping_address():
    """Checks if server_address address works by pinging it twice."""

    ping = subprocess.Popen(['ping', '-c', '2', slime_vars.server_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ping_out, ping_error = ping.communicate()
    if slime_vars.server_ip in str(ping_out) and ping_out.strip():
        return 'Success'
    return 'Unreachable'

# ========== File/folder editing/manipulation
def edit_file(target_property=None, value='', file_path=None):
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

    if not file_path: file_path = f"{slime_vars.server_path}/server.properties"
    try: os.chdir(slime_vars.server_path)
    except: pass
    if not os.path.isfile(file_path): return False
    return_line = ''

    # print() writes to file while using it in FileInput() with inplace=True
    # fileinput doc: https://docs.python.org/3/library/fileinput.html
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            split_line = line.split('=', 1)

            # If found match, and user passed in new value to update it.
            if target_property in split_line[0] and len(split_line) > 1:
                if value:
                    split_line[1] = value  # edits value section of line
                    new_line = return_line = '='.join(split_line)
                    print(new_line, end='\n')  # Writes new line to file
                # If user did not pass a new value to update property, just return the line from file.
                else:
                    return_line = '='.join(split_line)
                    print(line, end='')
            else: print(line, end='')

    # Returns value, and complete line
    if return_line:
        return return_line, return_line.split('=')[1].strip()
    else: return "Match not found.", 'Match not found.'

def read_json(json_file):
    """Read .json files."""
    with open(json_file) as file:
        return [i for i in json.load(file)]

def read_csv(csv_file):
    """Read .csv files in bot_files directory."""
    os.chdir(slime_vars.bot_filepath)
    with open(csv_file) as file:
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

def update_csv(csv_file, new_data=None):
    """Updates csv files in bot_files directory."""

    os.chdir(slime_vars.bot_filepath)

    with open(csv_file, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(new_data)

def convert_to_bytes(data): return io.BytesIO(data.encode())

def status_slime_proc():
    """Get bot process name and pid."""

    if proc := get_proc(slime_proc_name, slime_proc_cmdline):
        lprint(ctx, f"INFO: Process info: {proc.name()}, {proc.pid}")

def kill_slime_proc():
    """Kills bot process."""

    if proc := get_proc(slime_proc_name, slime_proc_cmdline):
        proc.kill()
        lprint(ctx, "INFO: Bot process killed")
    else: lprint(ctx, "ERROR: Bot process not found")

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
            if index_mode:
                # label, value, is default, description
                return_list.append([item, index, False, index])  # Need this for world/server commands
                index += 1
                continue
            if 's' in mode and item in slime_vars.servers:
                return_list.append([item, item, False, slime_vars.servers[item]['server_description']])  # For server mode for ?controlpanel command component
                index += 1
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

def update_server_paths(server_dict, server_name, text_to_replace=None):
    """
    Replaces 'SELECTED_SERVER' in server dict values if key has 'path' in it.
    """
    text_to_replace = 'SELECTED_SERVER'
    server_dict['server_name'] = server_name
    for k, v in server_dict.items():
        if 'path' in k:  # Replaces SELECTED_SERVER only if key has 'path' in it.
            server_dict[k] = v.replace(text_to_replace, server_name)

    return server_dict

def update_servers_vars():
    """Checks if there's new configs in 'example' and updates the other servers with defaults."""
    global slime_vars
    for name, data in slime_vars.servers.items():
        if 'example' in name: continue  # Skip example template
        server = slime_vars.servers['example'].copy()
        server.update(data)  # Updates example template values with user set ones, fallback on 'example' defaults
        server = update_server_paths(server, name)  # Updates paths (substitutes SELECTED_SERVER)
        # Updates slime_vars then writes to file.
        slime_vars.servers.update({name: server})
        slime_vars.update_vars(slime_vars.config)

def update_from_user_config(config):
    # Updates bot_config sub-dict. This will preserve manually added variables. It will add defaults of missing needed configs
    with open(slime_vars.user_config_filepath, 'r') as openfile:
        def deep_update(original_dict, update_dict):
            for key, value in update_dict.items():  # Updates nested dictionaries.
                if isinstance(value, dict) and key in original_dict and isinstance(original_dict[key], dict):
                    deep_update(original_dict[key], value)
                else: original_dict[key] = value
        deep_update(config, json.load(openfile))
    return config
