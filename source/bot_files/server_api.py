from bot_files.extra import lprint
from bot_files.slime_vars import config

class Server_Versioning:

    def get_server_version(self):
        """
        Gets server version, either by reading server log or using PINGClient.

        Returns:
            str: Server version number.
        """

        # Manual override of server version.
        if version := config.get('server_version'): return version

        elif config.get('server_files_access') is True:
            try: return server_log('server version').split('version')[1].strip()
            except: return 'N/A'
        return 'N/A'

    def download_official(self): pass

    def download_papermc(self): pass

    def downlaod_bukkit(self): pass

    def server_update(self): pass
    def server_update_check(self):
        """
        Gets latest Minecraft server version number from official website using bs4.

        Returns:
            str: Latest version number.
        """

        soup = BeautifulSoup(requests.get(config.get('new_server_address')).text, 'html.parser')
        for i in soup.findAll('a'):
            if i.string and 'minecraft_server' in i.string:
                return '.'.join(i.string.split('.')[1:][:-1])  # Extract version number.


class Server_API(Server_Versioning):
    def __init__(self):
        pass

    def _send_command(self): return False

    # ========== Servers and backups
    async def send_command(self, command, force_check=False, skip_check=False, discord_msg=True, ctx=None):
        """
        Sends command to Minecraft server. Depending on whether server is a subprocess or in Tmux session or using RCON.
        Sends command to server, then reads from latest.log file for output.
        If using RCON, will only return RCON returned data, can't read from server log.

        Args:
            command str: Command to send.
            force_check bool(False): Skips server_active boolean check, send command anyways.
            skip_check(False): Skips sending check command. E.g. For sending a lot of consecutive commands, to help reduces time.
            discord_msg bool(True): Send message indicating if server is inactive.

        Returns:
            bool: If error sending command to server, sends False boolean.
            list: Returns list containing match from server_log if found, and random_number used.
        """

        global mc_subprocess, server_active

        status = None

        # This is so user can't keep sending commands to RCON if server is unreachable. Use ?stat or ?check to actually check if able to send command to server.
        # Without this, the user might try sending multiple commands to an unreachable RCON server which will hold up the bot.
        if force_check is False and server_active is False: status = False

        if not skip_check:
            # Doesn't skip if returns None, means you can send command but can't get response
            if self.check_active() is False: return False

        # Create random number to send to server to be checked in logs.
        status_checker_command, random_number = config.get('status_checker_command'), str(random.random())
        status_checker = status_checker_command + ' ' + random_number

        self._send_command(command)


        elif config.get('use_tmux') is True or config.get('server_use_screen'):
            if config.get('check_before_command') is False: skip_check = True  # Don't send the 'xp' command.

            if not skip_check:  # Check if server reachable before sending command.
                # Checks if server is active in the first place by sending random number to be matched in server log.
                if config.get('server_use_screen'):  # Using screen to run/send commands to MC server.
                    os.system(f"screen -S {config.get('screen_session_name')} -X stuff '{status_checker}\n'")
                    # TODO CHCK
                else:  # Send to Tmux pane.
                    os.system(
                        f"tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} '{status_checker}' ENTER")
                await asyncio.sleep(config.get('command_buffer_time'))
                if not server_log(random_number): status = False

            if config.get('server_use_screen'):
                os.system(f"screen -S {config.get('screen_session_name')} -X stuff '{command}\n'")
            else:
                os.system(
                    f"tmux send-keys -t {config.get('tmux_session_name')}:{config.get('tmux_minecraft_pane')} '{command}' ENTER")

        if config.get('check_before_command') is True:
            _send_command()
        if status is False:
            msg = "**Server INACTIVE** :red_circle:\nUse `?check` to update server status."
            if discord_msg:
                try:
                    await ctx.send(msg)
                except:
                    await channel_send(msg)
            return False

        await asyncio.sleep(config.get('command_buffer_time'))
        # Returns log line that matches command.
        return_data = [server_log(command), random_number]
        # needs to return None because bot can't accurately get feedback.
        return return_data

    def get_status(self): pass

    def read_log(self): pass

class Server_Rcon_API(Server_API):
    def send_command(self, command): pass
    def get_status(self): pass

    def _get_server_version(self): pass

            try:
                return server_ping()['version']['name']
            except:
                return 'N/A'

    async def _send_command(self, command):
        """
        Send command to server with RCON.

        Args:
            command str(''): Minecraft server command.

        Returns:
            bool: Returns False if error connecting to RCON.
            str: Output from RCON.
        """

        global server_active

        server_rcon_client = mctools.RCONClient(config.get('server_address'), port=config.get('rcon_port'))
        try: server_rcon_client.login(config.get('rcon_pass'))
        except ConnectionError:
            lprint(ctx, f"Error Connecting to RCON: {config.get('server_ip')} : {config.get('rcon_port')}")
            server_active = False
            return False
        else:
            server_active = True
            return_data = server_rcon_client.command(command)
            server_rcon_client.stop()
            return return_data


class Server_Tmux_API(Server_API):


class Server_Screen_API(Server_API):


class Server_Subprocess_API(Server_API):
    # TODO be able to have multiple subprocess servers running and switch between them
    def _send_command(self, command):
        mc_subprocess.stdin.write(bytes(command + '\n', 'utf-8'))
        mc_subprocess.stdin.flush()
