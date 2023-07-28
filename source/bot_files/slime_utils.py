"""
Some utilities that don't exactly belong in any other module.
"""

import re
import io
import os
import csv
import json
import math
import shutil
import psutil
import random
import inspect
import requests
import datetime
import subprocess
from os import listdir
from os.path import isdir, isfile, join, exists

from typing import Union, Any, Tuple, List, Dict, Generator
import mctools
from discord.ext.commands import Context

from bot_files.slime_config import config
import bot_files.discord_components as components

enable_inputs = ['enable', 'activate', 'true', 'on']
disable_inputs = ['disable', 'deactivate', 'false', 'off']
slime_proc = slime_pid = None  # If using nohup to run bot in background.
slime_proc_name, slime_proc_cmdline = 'python3',  'slime_bot.py'  # Needed to find correct process if multiple python process exists.

def lprint(arg1: Union[Context, str], arg2:str = None) -> None:
    """
    Prints and Logs events in file.
    Logs who or where function/command was called.
    If received a ctx object, this will extract a username; else it'll get the filename of where the function originates.

    Args:
        arg1 (Discord Context, str): Either Discord context or a message.
        arg2 (Discord Context): Message if recieved Discord context also.
    """

    # Get Discord username if provided Context else gets filename of where lprint() is being called from.
    if isinstance(arg1, Context):
        ctx = arg1.message.author
        msg = arg2
    else:
        ctx = os.path.basename(inspect.stack()[1].filename)
        msg = arg1

    # Format date and print log message.
    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({ctx}): {msg}"
    print(output)

    # Logs output.
    with open(config.get_config('bot_log_filepath'), 'a') as file:
        file.write(output + '\n')


def status_slime_proc(self):
    """Get bot process name and pid."""

    if proc := utils.get_proc(slime_proc_name, slime_proc_cmdline):
        lprint(f"INFO: Process info: {proc.name()}, {proc.pid}")


def kill_slime_proc(self):
    """Kills bot process."""

    if proc := utils.get_proc(slime_proc_name, slime_proc_cmdline):
        proc.kill()
        lprint("INFO: Bot process killed")
    else:
        lprint("ERROR: Bot process not found")


class File_Utils:
    def test_file(self, file_path: str, check_writable: bool = False) -> bool:
        """
        Test if a file exists, if it's readable, and if it's writable.
        Will fail if file not readable (even if exists and writable).

        Args:
            file_path (str): The path of the file to test.
            mode (str): What to test for, 'rw', readable, writable.

        Returns:
            bool: If file passed testing based on the mode.
        """

        if not exists(file_path) or not os.access(file_path, os.R_OK):
            lprint(f"ERROR: File not found or not readable: {file_path}")
            return False
        if check_writable and not os.access(file_path, os.W_OK):
            return False
        return True

    def read_file_generator(self, file_path: str) -> Generator[str, None, None]:
        """
        Yield file lines (top to bottom).

        Args:
            file_path (str): File path to yield lines.

        Returns:
            str: Yields a line from file
        """

        if not self.test_file(file_path): return False
        with open(file_path, 'r') as file:
            for line in file:
                yield line

    def read_file_reverse_generator(self, file_path: str) -> Generator[str, None, None]:
        """
        Yield file lines (bottom to top).

        Args:
            file_path (str): File to yield line starting from bottom.

       Returns:
            str: A line from file.
        """

        if not self.test_file(file_path): return False
        with open(file_path, 'r') as file:
            file.seek(0, os.SEEK_END)  # Move the file pointer to the end of the file.
            file_size = file.tell()  # Get the current file pointer position (end of the file).

            # Start reading the file in reverse line by line.
            while file.tell() > 0:
                file.seek(-1, os.SEEK_CUR)  # Move one character back from the current position.
                current_char = file.read(1)  # Read the character at the current position.

                # If we find a newline character or reach the beginning of the file, yield the line.
                if current_char == '\n' or file.tell() == 0:
                    line = file.readline().rstrip('\n')
                    yield line[::-1]  # Reverse the line before yielding.
                else: file.seek(-1, os.SEEK_CUR)  # Move one character back to include the newline character in the line.

    def read_json(self, file_path: str) -> Union[List[Dict[str, Any]], bool]:
        """
        Returns list of data from .json files.

        Args:
            file_path str: File to read.

        Returns:
            list, bool: Returns a list of json dict data, or a False if anything failed.
        """


        if not self.test_file(file_path): return False
        try:
            with open(file_path) as file:
                return [i for i in json.load(file)]
        except: return False

    def write_json(self, file_path: str, data: dict) -> bool:
        """
        Write data to json file.

        Args:
            file_path str: File path to write json data to.
            data dict: Dictionary data to write to file.

        Returns:
            bool: Whether if succesful or not.
        """

        if not self.test_file(file_path): return False
        try:
            with open(file_path, "w") as outfile:
                outfile.write(json.dumps(data, indent=4))
        except:
            lprint(f"ERROR: Problem writing to json file: {file_path}")
            return False
        return True

    def read_csv(self, file_path: str) -> Union[List, bool]:
        """
        Get data from csv file.

        Args:
            file_path str: Path of file.

        Returns:
            list, bool: List of csv data or False if failed.
        """

        if not self.test_file(file_path): return False
        with open(file_path) as file:
            return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

    def write_csv(self, file_path: str, data: list) -> bool:
        """
        Write datat o csv file.

        Args:
            file_path str: Path of file.
            data list: data to write to csv.

        Returns:
            bool: If successful.
        """

        if not self.test_file(file_path): return False
        try:
            with open(file_path, 'w') as file:
                csv.writer(file).writerows(data)
        except: return False

        return True

    def get_from_index(self, path: str, index: int, mode: str) -> str:
        """
        Get server or world backup folder name from passed in index number

        Args:
            path str: Path to search through.
            index int: Select specific folder/file by index, get index from commands like ?worldbackupslist, ?serverbackupslist
            mode str: Only get files or folders.

        Returns:
                str: Path of selected.
        """

        items = ['placeholder']  # Listed items in Discord (select menus, embeds) start at 1 (for user convients). But python is 0, soooo, yeah. need this.
        for i in reversed(sorted(listdir(path))):
            if 'f' in mode and isfile(join(path, i)):
                items.append(i)
            elif 'd' in mode and isdir(join(path, i)):
                items.append(i)
            else: continue
        try:
            return f'{path}/{items[index]}'
        except: return ''

    # TODO Test (everything)
    def enum_dirs_for_discord(self, path: str, mode: str, index_mode: bool = False):
        """
        Returns a list containing index for folder/file in a path with variables for Discord select component.

        Args:
            path str: Path of world or server backups location.
            mode str: Aggregate only files or only directories.
            index_mode bool: Put index as second item in list.

        Returns:
            list: Data for Discord select component.
        """

        return_list = []
        if not isdir(path): return []

        index = 1
        for item in reversed(sorted(listdir(path))):
            # Appends only either file or directory to items list.
            flag = False
            if 'f' in mode and isfile(join(path, item)): flag = True
            elif 'd' in mode and isdir(join(path, item)): flag = True

            if flag:
                component_data = [item, index, False, index]
                if index_mode:
                    # label, value, is default, description
                    return_list.append(component_data)  # Need this for world/server commands
                    index += 1
                    continue
                if 's' in mode and item in config.servers:
                    component_data[-1] = config.get_server_configs(item)['server_description']
                    return_list.appen(component_data)  # For server mode for ?controlpanel command component
                    index += 1
                    continue
                return_list.append(component_data)  # Last 2 list items is for new_selection.
            else: continue
        return return_list

    def delete_dir(self, path: str) -> bool:
        """
        Delete directory.

        Args:
            backup str: Path direcotry to delete.

        Returns:
            bool: If successful.
        """

        try: shutil.rmtree(path)
        except: return False
        return True

    def new_dir(self, path: str) -> bool:
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            path str: Path to create new directory.

        Returns:
            bool: If successfully created new dir at path.
        """

        try:
            os.mkdir(path)
        except:
            return False
        return True

    def copy_dir(self, path: str, new_path: str) -> bool:
        """

        Args:
            path:
            new_path:

        Returns:

        """

        try:
            shutil.copytree(path, new_path)
        except:
            return False
        return True

    def move_dir(self, path: str, new_path: str) -> bool:
        """
        Copies then delete original.

        Args:
            path: Directory to move.
            new_path: Where to move to.

        Returns:
            bool: If successfully copied and deleted original.
        """

        if not self.copy_dir(path, new_path) and not self.delete_dir(path):
            return False
        return True


class Utils:

    # Get command and unique number used to check if server console reachable.
    def get_check_command(self) -> Tuple:
        """

        Returns:

        """

        random_number = str(random.random())
        status_check_command = config.get_config('status_checker_command') + ' ' + random_number
        return status_check_command, random_number

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
            config.set_config('server_ip', server_ip)
        except: return None
        return server_ip

    def ping_address(self, address: str) -> bool:
        """
        Checks if server_address address works by pinging it twice.

        Args:
            address (str): Address to ping.

        Returns:
            bool: If successful.
        """

        if config.get_config('windows_compatibility') is True:  # If on windows.
            try:
                if 'TTL=' in subprocess.run(["ping", "-n", "2", address], capture_output=True, text=True, timeout=10).stdout:
                    return True
            except: return False
        else:
            # TODO: FIX
            ping = subprocess.Popen(['ping', '-c', '2', address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ping_out, ping_error = ping.communicate()
            if ping_out.strip():
                print('te', ping_out)
                return True
            return False

    def convert_to_bytes(data): return io.BytesIO(data.encode())



utils = Utils()
file_utils = File_Utils()