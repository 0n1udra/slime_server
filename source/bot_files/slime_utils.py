"""
Some utilities that don't exactly belong in any other module.
"""

import re
import io
import os
import csv
import json
import math
import time
import socket
import shutil
import random
import asyncio
import inspect
import datetime
import traceback

from os import listdir
from os.path import isdir, isfile, join, exists

from typing import Union, Any, Tuple, List, Dict, Generator

from bot_files.slime_config import config

if config.get_config('use_pyenv'):
    try:
        import psutil, requests
    except Exception as e:
        print("ERROR: Missing modules")
        print(e)
    else: import psutil, requests

slime_proc = slime_pid = None  # If using nohup to run bot in background.
slime_proc_name, slime_proc_cmdline = 'python3',  'slime_bot.py'  # Needed to find correct process if multiple python process exists.

def lprint(arg1: Union[Any, str], arg2:str = None) -> None:
    """
    Prints and Logs events in file.
    Logs who or where function/command was called.
    If received a ctx object, this will extract a username; else it'll get the filename of where the function originates.

    Args:
        arg1 (Discord Context, str): Either Discord context or a message.
        arg2 (Discord Context): Message if recieved Discord context also.
    """

    # Get Discord username if provided Context else gets filename of where lprint() is being called from.
    try:
        ctx = arg1.message.author
        msg = arg2
    except:
        ctx = os.path.basename(inspect.stack()[1].filename)
        msg = arg1

    # Format date and print log message.
    output = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ({ctx}): {msg}"
    print(output)

    # Logs output.
    with open(config.get_config('bot_log_filepath'), 'a+') as file:
        file.write(output + '\n')


class File_Utils:
    def test_file(self, file_path: str, check_writable: bool = False) -> bool:
        """
        Test if a file exists, if it's readable, and if it's writable.
        Will fail if file not readable (even if exists and writable).

        Args:
            file_path (str): The path of the file to test.
            check_writable bool(False): Checks if able to write to file.

        Returns:
            bool: If file passed testing based on the mode.
        """

        if not exists(file_path) or not os.access(file_path, os.R_OK):
            lprint(f"ERROR: File not found or not readable: {file_path}")
            return False

        if check_writable and not os.access(file_path, os.W_OK):
            return False

        return True

    def test_dir(self, dir_path) -> bool:
        """
        Check if file path is reachable.

        Args:
            dir_path:

        Returns:
            bool: If file path exists.

        """

        # TODO: Possibly add if writable arg.
        if os.path.isdir(dir_path):
            return True

        return False

    def read_file_generator(self, file_path: str, lines: int = None) -> Union[Generator[str, None, None], bool]:
        """
        Yield file lines (top to bottom).

        Args:
            file_path (str): File path to yield lines.
            lines int(None): How many lines to return. None for all.

        Yields:
            str: File line.

        Returns:
            bool: If file not readable.
        """

        if not self.test_file(file_path):
            return False

        line_counter = 0
        with open(file_path, 'r') as file:
            for line in file:
                yield line
                line_counter += 1
                if lines is not None and line_counter >= lines:
                    break

    def read_file_reverse_generator(self, file_path: str, lines: int = None) -> Union[Generator[str, None, None], bool]:
        """
        A generator that returns the lines of a file in reverse order.
        Used for getting latest console log output.

        Args:
            file_path (str): File path to yield lines.
            lines int(None): How many lines to return. None for all.

        Yields:
            str: File line.

        Returns:
            bool: If file not readable.
        """

        buf_size = 8192
        line_counter = 0
        with open(file_path, 'rb') as fh:
            segment = None
            offset = 0
            fh.seek(0, os.SEEK_END)
            file_size = remaining_size = fh.tell()
            line_counter += 1
            lines_yielded = 0  # Counter for the number of lines yielded
            while remaining_size > 0:
                if lines is not None and lines_yielded >= lines:
                    break  # Stop generating lines if we have reached the desired number
                offset = min(file_size, offset + buf_size)
                fh.seek(file_size - offset)
                buffer = fh.read(min(remaining_size, buf_size)).decode(encoding='utf-8')
                remaining_size -= buf_size
                _lines = buffer.split('\n')
                if segment is not None:
                    if buffer[-1] != '\n':
                        _lines[-1] += segment
                    else:
                        yield segment
                segment = _lines[0]
                for index in range(len(_lines) - 1, 0, -1):
                    if _lines[index]:
                        if lines is not None and lines_yielded >= lines:
                            break  # Stop generating lines if we have reached the desired number
                        yield _lines[index]
                        lines_yielded += 1

    def read_json(self, file_path: str) -> Union[List[Dict[str, Any]], bool]:
        """
        Returns list of data from .json files.

        Args:
            file_path str: File to read.

        Returns:
            list, bool: Returns a list of json dict data, or a False if anything failed.
        """


        if not self.test_file(file_path):
            return False

        try:
            with open(file_path) as file:
                return [i for i in json.load(file)]
        except:
            return False

    def write_json(self, file_path: str, data: dict) -> bool:
        """
        Write data to json file.

        Args:
            file_path str: File path to write json data to.
            data dict: Dictionary data to write to file.

        Returns:
            bool: Whether if succesful or not.
        """

        try:
            with open(file_path, "w") as outfile:
                outfile.write(json.dumps(data, indent=4))
        except:
            lprint(f"ERROR: Problem writing to json file: {file_path}")
            traceback.print_exc()
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

        if not self.test_file(file_path):
            return False

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

        if not self.test_file(file_path):
            return False

        try:
            with open(file_path, 'w') as file:
                csv.writer(file).writerows(data)
        except:
            traceback.print_exc()
            return False

        return True

    def get_from_index(self, path: str, index: int, mode: str) -> Union[str, bool]:
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
        except: return False

    # TODO Test (everything)
    def enum_dirs_for_discord(self, path: str, mode: str):
        """
        Returns a list containing index for folder/file in a path with variables for Discord select component.

        Args:
            path str: Path of world or server backups location.
            mode str: Aggregate only files or only directories.

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
                component_data = [item, item, False, index]
                # For control panel in Server mode, need to show server description in select component options.
                if 's' in mode:
                    if item not in config.servers: continue
                    component_data[-1] = config.servers[item]['server_description']
                # For world/server backup mode in control panel, need to be return the index of selected.
                if 'b' in mode:
                    component_data[1] = index

                return_list.append(component_data)  # Last 2 list items is for new_selection.
                index += 1
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
        except:
            lprint(f"ERROR: Issue deleting folder: {path}")
            traceback.print_exc()
            return False

        return True

    def new_dir(self, path: str) -> Union[bool, None]:
        """
        Create a new world or server backup, by copying and renaming folder.

        Args:
            path str: Path to create new directory.

        Returns:
            bool, None: If successfully created new dir at path. None if folder already exists.
        """

        if os.path.isdir(path):
            lprint(f"ERROR: Folder already exist: {path}")
            return None
        try:
            os.mkdir(path)
        except:
            lprint(f"ERROR: Issue creating new folder: {path}")
            traceback.print_exc()
            return False
        lprint(f"INFO: New folder: {path}")
        return True

    def copy_dir(self, path: str, new_path: str) -> bool:
        """
        Copy directory to path.

        Args:
            path str: Source path.
            new_path str: Destination path.

        Returns:
            bool: If successful.
        """

        if not self.test_dir(path):
            lprint(f"ERROR: Could not copy folder, does not exist: {path}")
            return False

        try:
            shutil.copytree(path, new_path)
        except:
            lprint(f"ERROR: Issue copying folder: {path} > {new_path}")
            traceback.print_exc()
            return False
        lprint(f"INFO: Copied folder: {path} > {new_path}")
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

    def setup_directories(self) -> None:
        """Create necessary directories, servers, world_backups, server_backups."""

        # Creates Server folder, folder for world backups, and folder for server backups.
        self.new_dir(f"{config.get_config('home_path')}//Games")
        self.new_dir(config.get_config('mc_path'))
        self.new_dir(config.get_config('servers_path'))
        self.new_dir(f"{config.get_config('mc_path')}//server_backups")
        self.new_dir(f"{config.get_config('mc_path')}//world_backups")


class Proc_Utils:
    def get_proc(self, proc_name, proc_cmdline=None):
        """Returns a process by matching name and argument."""

        for proc in psutil.process_iter():
            if proc.name() == proc_name:
                # Narrow down process by its arguments. E.g. python3 could have multiple processes.
                if proc_cmdline:
                    if any(proc_cmdline in i for i in proc.cmdline()):
                        return proc
                else: return proc

    def status_slime_proc(self):
        """Get bot process name and pid."""

        if proc := self.get_proc(slime_proc_name, slime_proc_cmdline):
            lprint(f"INFO: Process info: {proc.name()}, {proc.pid}")

    def kill_slime_proc(self):
        """Kills bot process."""

        if proc := self.get_proc(slime_proc_name, slime_proc_cmdline):
            proc.kill()
            lprint("INFO: Bot process killed")
        else:
            lprint("ERROR: Bot process not found")


class Utils:
    enable_inputs = ['enable', 'activate', 'true', 'on']
    disable_inputs = ['disable', 'deactivate', 'false', 'off']

    def parse_opadd_output(self, output: str, username: str) -> Union[bool, None]:
        """


        Args:
            output:

        Returns:

        """

        added_keywords = ['a server operator', 'INFO]: Opped']
        already_added_keywords = ['Nothing changed. The player already is an operator']

        if any(i in output for i in already_added_keywords):
            return None

        if username.lower() in output.lower() and any(i in output for i in added_keywords):
            return True

        return False

    def parse_deop_output(self, output: str, username: str) -> Union[bool, None]:
        """


        Args:
            output:

        Returns:

        """

        removed_keywords = ['no longer a server operator']
        already_removed_keywords = ['Nothing changed. The player is not an operator']

        if any(i in output for i in already_removed_keywords):
            return None

        if username.lower() in output.lower() and any(i in output for i in removed_keywords):
            return True

        return False

    def parse_players_output(self, output: str, version: str) -> Union[Tuple[List[str], str], bool, None]:
        """
        Extracts wanted data from output of 'list' command.
        Console output is different based on types and versions.

        Args:
            output list: Command output lines.
            version str: Minecraft version string.

        Returns:
            tuple, str or bool: Tuple of player names and console text, or False.
        """

        # Only gets the second number. E.g. 1.12.2 > 12, 1.14 > 14
        try:
            version = float(version.split('.')[1])
        except: version = 20

        # In version 1.12 and lower, the /list command outputs usernames on a newline from the 'There are x players' line.
        if version <= 12:
            # Parses and returns info from log lines.
            try:
                text = output[1].split(':')[-2].strip()
                player_names = output[0].split(':')[-1].split(',')
                return player_names, text
            except:
                return None
        else:
            if config.get_config('server_use_essentialsx'):
                text = output[-1].split(':')[-1].strip()  # There are 2 of a max of 20 players online
                player_names = []
                for line in output[:-1]:
                    names_section = line.split(':')[-1].strip()
                    player_names += [i.strip() for i in names_section.split(',')]
                    print("LINE", player_names)
                    return player_names, text
            else: return False

            # TODO make get_command_output be able to take command
            try:
                reaesc = re.compile(r'\x1b[^m]*m')
                # Use regular expression to extract player names
                output = output[0].split(':')  # [23:08:55 INFO]: There are 2 of a max of 20 players online: R3diculous, MysticFrogo
                text = output[-2]  # There are 2 of a max of 20 players online
                text = reaesc.sub('', text)  # Remove unwanted escape characters
                player_names = output[-1]  # R3diculous, MysticFrogo
                # If there's no players active, player_names will still contain some anso escape characters.
                if len(player_names.strip()) < 5:
                    return None
                else:
                    player_names = [f"{i.strip()[:-4]}\n" if config.get_config('use_rcon') else f"{i.strip()}" for i in (output[-1]).split(',')]
                    # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
                    # player_names_discord = [f"`{i.strip()[:-4]}`\n" if use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]
                    new = []
                    for i in player_names:
                        x = reaesc.sub('', i).strip().replace('[3', '')
                        x = x.split(' ')[-1]
                        x = x.replace('\\x1b', '').strip()
                        new.append(x)
                    player_names = new
                    return player_names, text
            except:
                return False

    def parse_version_output(self, output: str) -> Union[str, bool]:
        """

        Args:
            output:

        Returns:

        """

        if 'Paper' in output:
            return output.split('MC:')[1].split(')')[0].strip()

        return False

    # Get command and unique number used to check if server console reachable.
    def get_check_command(self) -> Tuple:
        """
        Creates command containing random number to send to console, to use as a stopgap when reading log file.

        Returns:
            str, str: Command to send, and the random number generated.
        """

        random_number = str(random.random())
        command = config.get_config('status_checker_command')
        if config.get_config('server_use_essentialsx'):
            command = 'ping'
        status_check_command = f'{command} {random_number}'
        return status_check_command, random_number

    def get_parameter(self, arg, nrg_msg: bool = False, key: str = 'second_selected', **kwargs) -> str:
        """
        Gets needed parameter for function to run properly.
        Discord commands can be called from buttons or prefix command.
        If using prefix command, it'll just format the parameters as needed.
        If function being called from button, will get needed parameter using components.data func.

        Args:
            arg: Will either receive parameters from using prefix, or will be bmode.
            nrg_msg bool: Returns 'No reason given' string, if arg is empty.
            key str: Key of data dict to get parameter from. Used for getting selection from components.

        Returns:
            str: Needed data to use as parameters for bot command.
        """

        # Checks if command was called from button
        if 'bmode' in arg:
            from bot_files.discord_components import comps
            from_data_dict = comps.get_data(key)
            if from_data_dict:
                comps.set_data(key, None)
                return from_data_dict

        elif type(arg) in (list, tuple):
            return ' '.join(arg)

        if not arg: return ''
        if nrg_msg and not arg: return "No reason given."

        return arg

    def group_items(self, items, size: int = 25) -> Union[Tuple[List, int], Tuple[None, None]]:
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

    def format_args(self, args: tuple, return_no_reason: bool = False) -> str:
        """
        Formats passed in *args from Discord command functions.
        This is so quotes aren't necessary for Discord command arguments.

        Args:
            args tuple: Data to combine into single str for bot command.
            return_no_reason bool(False): returns string 'No reason given.' for commands that require a reason (kick, ban, etc).

        Returns:
            str: Arguments combines with spaces.
        """

        if args:
            return ' '.join(args)
        else:
            if return_no_reason:
                return "No reason given."
            return ''

    def get_datetime(self) -> str:
        """
        Returns date and time: 2021-12-04 01-49

        Returns:
            str: Formatted time date.
        """

        return datetime.datetime.now().strftime('%Y-%m-%d %H-%M')

    def remove_ansi(self, text: str) -> str:
        """
        Removes ANSI escape characters.

        Returns:
            str: Formatted string.
        """

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def print_dict_data(self, data: dict, indent: int = 0) -> str:
        """
        Formats dictionary data into single string with indents.
        Indents for nesting dictionary data.

        Args:
            data: Dictionary with data to format.
            indent: How many indents when found nested dict. This is for when function self calls.

        Returns:
            str: Formatted data.
        """
        # TODO Fix indentation
        result = ''
        for key, value in data.items():
            if isinstance(value, dict):
                result += f'    {key}:\n'
                result += self.print_dict_data(value, indent + 4)
            else:
                result += ' ' * indent + f'{key}: {value}\n'
        return result

    def get_public_ip(self) -> Union[str, None]:
        """
        Returns your public IP address.

        Returns:
            str, bool: IP address if fetched, else False.
        """

        try:
            server_ip = json.loads(requests.get('http://jsonip.com').text)['ip']
            config.set_config('server_ip', server_ip)
        except: return None
        return server_ip

    async def ping_address(self, address: str) -> Union[str, bool]:
        """
        Checks if server_address address works by pinging it twice.

        Args:
            address (str): Address to ping.

        Returns:
            bool: If successful.
        """
        try:
            start_time = time.time()
            reader, writer = await asyncio.open_connection(address, 80)
            writer.close()
            await writer.wait_closed()
            elapsed_time = (time.time() - start_time) * 10
            config.failed_pings = 0
            return str(elapsed_time)
        except (socket.timeout, ConnectionError):
            if config.failed_pings < config.failed_ping_limit:
                lprint(f"ERROR: Failed to ping: {address}")
                config.failed_pings += 1

        return False

    def convert_to_bytes(self, data: Any) -> io.BytesIO:
        """
        Converts data to ByteIO data.
        Mainly used for formatting data to be sent as a Discord file attachment.

        Args:
            data: Data to convert.

        Returns:
            ByteIO: io.ByteIO data.
        """

        return io.BytesIO(data.encode())

    def start_tmux_session(self, tmux_session_name: str) -> Union[bool, None]:
        """
        Starts Tmux session in detached mode, with 2 panes, and sets name.

        Args:
            tmux_session_name str: Name of new tmux session.

        Returns:
            bool: If successful.
        """

        # If tmux session already exists.
        if not os.system(f"tmux ls | grep {tmux_session_name}"):
            lprint("INFO: Tmux session already exists.")
            return None

        if os.system(f"tmux new -d -s {tmux_session_name}"):
            lprint(f"ERROR: Starting tmux session: {tmux_session_name}")
            return False
        else: lprint(f"INFO: Started Tmux detached session: {tmux_session_name}")

        if os.system(f"tmux split-window -v -t {tmux_session_name}:0.0"):
            lprint(f"ERROR: Creating second tmux panes: {tmux_session_name}")
            return False
        else: lprint(f"INFO: Created second tmux panes: {tmux_session_name}")

        time.sleep(1)
        return True

file_utils = File_Utils()
proc_utils = Proc_Utils()
utils = Utils()
