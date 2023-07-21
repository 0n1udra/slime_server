import subprocess, fileinput, requests, datetime, shutil, psutil, json, math, csv, os, re, io
import mctools
from bot_files.slime_vars import config
from bot_files.backend_functions import backend
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
    ping = mctools.PINGClient('address', 25565)
    stats = ping.get_stats()
    print(stats)
    ping.stop()
    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({user}): {msg}"
    print(output)

    # Logs output.
    with open(config.get('bot_log_filepath'), 'a') as file:
        file.write(output + '\n')


def status_slime_proc(self):
    """Get bot process name and pid."""

    if proc := get_proc(slime_proc_name, slime_proc_cmdline):
        lprint(ctx, f"INFO: Process info: {proc.name()}, {proc.pid}")


def kill_slime_proc(self):
    """Kills bot process."""

    if proc := get_proc(slime_proc_name, slime_proc_cmdline):
        proc.kill()
        lprint(ctx, "INFO: Bot process killed")
    else:
        lprint(ctx, "ERROR: Bot process not found")


class File_Utils:
    def read_json(self, json_file):
        """Read .json files."""
        with open(json_file) as file:
            return [i for i in json.load(file)]

    def update_json(self, data): pass

    def read_csv(self, csv_file):
        """Read .csv files in bot_files directory."""
        os.chdir(config.get('bot_filepath'))
        with open(csv_file) as file:
            return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

    def update_csv(self, csv_file, new_data=None):
        """Updates csv files in bot_files directory."""

        os.chdir(config.get('bot_filepath'))

        with open(csv_file, 'w') as file:
            writer = csv.writer(file)
            writer.writerows(new_data)

    def get_from_index(self, path, index, mode):
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

    def enum_dir(self, path, mode, index_mode=False):
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
                if 's' in mode and item in config.get('servers'):
                    return_list.append([item, item, False, backend.get_server(item)['server_description']])  # For server mode for ?controlpanel command component
                    index += 1
                    continue
                return_list.append([item, item, False, index])  # Last 2 list items is for new_selection.
            else: continue
        return return_list

    def delete_dir(self, backup):
        """
        Delete world or server backup.

        Args:
            backup str: Path of backup to delete.
        """

        shutil.rmtree(backup)


class Utils(File_Utils, Proc_Utils):

    def new_server(self, name):
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.
            src str: Folder to backup, whether it's a world folder or a entire server folder.
            dst str: Destination for backup.
        """

        new_folder = join(config.get('servers_path'), name.strip())
        os.mkdir(new_folder)
        return new_folder

    def new_backup(self, new_name, src, dst):
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            new_name str: Name of new copy. Final name will have date and time prefixed.
            src str: Folder to backup, whether it's a world folder or a entire server folder.
            dst str: Destination for backup.
        """

        if not os.path.isdir(dst): os.makedirs(dst)
        # TODO add multiple world folders backup
        # folder name: version tag if known, date, optional name
        version = f"{'v(' + server_version() + ') ' if 'N/A' not in server_version() else ''}"
        new_name = f"({extra.get_datetime()}) {version}{new_name}"
        new_backup_path = join(dst, new_name.strip())
        shutil.copytree(src, new_backup_path)
        return new_backup_path

    def restore_backup(self, src, dst):
        """
        Restores world or server backup. Overwrites existing files.

        Args:
            src str: Backed up folder to copy to current server.
            dst str: Location to copy backup to.
        """

        shutil.rmtree(dst)
        shutil.copytree(src, dst)


    def get_parameter(self, arg, nrg_msg=False, key='second_selected', **kwargs):
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

    def group_items(self, items, size=25):
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

    def get_proc(self, proc_name, proc_cmdline=None):
        """Returns a process by matching name and argument."""

        for proc in psutil.process_iter():
            if proc.name() == proc_name:
                # Narrow down process by its arguments. E.g. python3 could have multiple processes.
                if proc_cmdline:
                    if any(proc_cmdline in i for i in proc.cmdline()):
                        return proc
                else: return proc

    def format_args(self, args, return_no_reason=False):
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

    def format_coords(self, coordinates):
        pass

    def get_datetime(self):
        """Returns date and time. (2021-12-04 01-49)"""

        return datetime.datetime.now().strftime('%Y-%m-%d %H-%M')

    def remove_ansi(self, text):
        """Removes ANSI escape characters."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def get_public_ip(self):
        """Gets your public IP address, to updates server ip address varable using request.get()"""

        global server_ip
        try:
            server_ip = json.loads(requests.get('http://jsonip.com').text)['ip']
            config.get('server_ip') = server_ip
        except: return None
        return server_ip

    def ping_address(self):
        """Checks if server_address address works by pinging it twice."""

        ping = subprocess.Popen(['ping', '-c', '2', config.get('server_address')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ping_out, ping_error = ping.communicate()
        if config.get('server_ip') in str(ping_out) and ping_out.strip():
            return 'Success'
        return 'Unreachable'

    # ========== File/folder editing/manipulation


    def convert_to_bytes(data): return io.BytesIO(data.encode())


