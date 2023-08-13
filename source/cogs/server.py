import asyncio
from os import listdir
from os.path import join, isdir, isfile

import discord
from discord.ext import commands, tasks

from bot_files.slime_backend import backend
from bot_files.slime_config import config
from bot_files.slime_utils import lprint, utils
from bot_files.discord_components import comps


# ========== Server: autosave, Start/stop, Status, edit property, backup/restore.
class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # TODO make autosave multi server compatible somehow....
        if config.get_config('enable_autosave'):
            self.autosave_task.start()
            lprint(f"Autosave task started (interval: {config.get_config('autosave_interval')}m)")

    # ===== Servers, new, delete, editing, etc
    @commands.command(aliases=['select', 'sselect', 'selectserver', 'serverslist', 'ss', 'servers', 'listservers'])
    async def serverselect(self, ctx, *name):
        """
        Select server to use all other commands on. Each server has their own world_backups and server_restore folders.
        This command is also used to list available servers.

        Args:
            name: name of server to select, use ?selectserver list or without arguments to show list.

        Usage:
            ?selectserver list
            ?selectserver papermc
        """

        if 'bmode' in name:
            name = comps.get_data('second_selected')
            if not name: return
        else: name = utils.format_args(name)

        if not name and 'list' not in name:
            await backend.send_msg(f"**Current Server:** `{config.get_config('server_name')}`")
            await backend.send_msg(f"Use `?serverselect list` or `?ss list` to list servers, and `?ss server_name` to switch.")
        elif 'list' in name:
            embed = discord.Embed(title='Server List :desktop:')
            for server, sdata in config.servers.items():
                # Shows server name, description, location, and Launch Command.
                embed.add_field(name=sdata['server_name'], value=f"Description: {sdata['server_description']}\nLocation: `{sdata['server_path']}`\nLaunch Command: `{sdata['server_launch_command']}`", inline=False)
            await backend.send_msg(embed=embed)
            await backend.send_msg(f"**Current Server:** `{config.server_configs['server_name']}`")
            await backend.send_msg(f"Use `?serverselect` to list, or `?ss [server]` to switch.")
        elif name in config.servers:
            if not config.get_config('players_custom_status'):
                await self.bot.change_presence(activity=discord.Activity(name=f"- {config.server_configs['server_name']}", type=1))
            await backend.select_server(name)
            await backend.send_msg(f"**Selected Server:** {name}")
        else: await backend.send_msg("**ERROR:** Server not found.")

    @commands.command(aliases=['si'])
    async def serverinfo(self, ctx, *name):
        """Embed of server information."""

        server_name = utils.get_parameter(name)

        # if get_parameter() returning bmode tuple, means no server was selected or server name given
        if 'bmode' in server_name:
            await backend.send_msg("No info to get.")
            return

        if data := config.servers.get(server_name, config.server_configs):
            fields = [['API Interface', backend.server_api.current_api]]
            for k, v in data.items():
                if isinstance(k, dict): continue
                fields += [[k, v]]
            await backend.send_msg(embed=comps.new_embed(fields, 'Server Info'))
            lprint("Fetched server info")
        else:
            await backend.send_msg("**ERROR:** No server info.")
        return False

    @commands.command(hidden=True)
    async def servernew(self, ctx, interaction):
        """Create new server. Only works from control panel."""

        if interaction == 'submitted':
            await backend.send_msg("***Creating New Server...***")

            data_from_modal = comps.get_data('servernew')
            new_server_name = data_from_modal['server_name']

            if new_server_name in config.servers:
                await backend.send_msg("Server name already used.")
                return

            # Tries to create new folder.
            if isdir(join(config.get_config('servers_path'), new_server_name)):
                await backend.send_msg(f"Folder `{new_server_name}` already exists. Use `?sscan` to add it and create configs for it..")
            else:
                if not await backend.server_new(new_server_name, data_from_modal):
                    await backend.send_msg("**Error**: Issue creating server.")
                    lprint(ctx, f"ERROR: Creating server: {new_server_name}")
                    return

            # Adds new server to servers dict.
            await ctx.invoke(self.bot.get_command('serverinfo'), new_server_name)

            try: await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')
            except: pass
            await backend.send_msg("Use `?selectserver` to use bot commands on new server.")

        else:
            modal_msg = await interaction.response.send_modal(comps.new_modal(comps.server_modal_fields('example'), 'New Server', 'servernew'))

    @commands.command(hidden=True)
    async def serveredit(self, ctx, interaction):
        """Edit server information. Updates servers.csv file."""

        # This only works with control panel right. This gets selected server's name.
        server_name = comps.get_data('second_selected')
        if not server_name:
            await backend.send_msg("No server selected.")
            return

        if interaction == 'submitted':
            new_data = comps.get_data('serveredit')

            # Gets current configs for server to be used to update new configs..
            if not await backend.server_edit(server_name, new_data):
                await backend.send_msg("**ERROR:** Problem editing server configs.")
                return False

            await ctx.invoke(self.bot.get_command('serverinfo'), new_data['server_name'])
            try: await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')
            except: pass
        else:  # Sends modal dialog to input info
            # Creates server config if not exist. NOTE: Does not update json file unless modal is submitted and accepted.
            if server_name not in config.servers:
                config.new_server_configs(server_name)

            modal_msg = await interaction.response.send_modal(comps.new_modal(comps.server_modal_fields(server_name), 'New Server', 'serveredit'))

    @commands.command(hidden=True)
    async def servercopy(self, ctx, interaction):
        """Copy server. Only works from control panel for now."""

        server_name = comps.get_data('second_selected')

        if not server_name:
            await backend.send_msg("No server selected.")
            return

        if interaction == 'submitted':
            new_data = comps.get_data('servercopy')

            if new_data['server_name'] in config.servers:
                await backend.send_msg(f"**ERROR:** Server name already in use: {server_name}")
                return

            await backend.send_msg("***Copying Server...***")
            if await backend.server_copy(server_name, new_data['server_name']) is False:
                lprint(ctx, f"ERROR: Issue copying server: {server_name} > {new_data['server_name']}")
                return False

            await ctx.invoke(self.bot.get_command('serverinfo'), new_data['server_name'])

            try: await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')
            except: pass
        else:
            modal_msg = await interaction.response.send_modal(comps.new_modal(comps.server_modal_fields(server_name), 'Copy Server', 'servercopy'))

    @commands.command(aliases=['sd', 'deleteserver'])
    async def serverdelete(self, ctx, *name):
        """
        Delete a server.

        Args:
            name: Server to delete. Case sensitive!

        Usage:
            ?serverdelete papermc
            ?sd valhesia 3
        """

        server_name = utils.get_parameter(name)
        if not server_name:
            await backend.send_msg("No server selected.")
            return

        if await backend.server_delete(server_name) is False:
            await backend.send_msg(f"**Error:** Issue deleting server: `{server_name}`")
            return
        await backend.send_msg(f"**Server Deleted:** `{server_name}`")
        lprint(ctx, f"Deleted server: {server_name}")

        if 'bmode' in name:
            try: await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')
            except: pass

    @commands.command(aliases=['sscan'])
    async def serverscan(self, ctx, *name):
        """
        Check if new serer folder has been added.

        Usage:
            ?serverscan
            ?sscan
        """

        new_servers_found = False

        await backend.send_msg("***Scanning for new servers...***")
        for folder in listdir(config.get_config('servers_path')):
            # Checks if server already in 'slime_vars.servers' dict, and if 'folder' is actually a folder.
            if folder not in config.servers and isdir(join(config.get_config('servers_path'), folder)):
                config.new_server_configs(folder)  # Create new folder and configs.

                await backend.send_msg(f"**added:** `{folder}`")
                lprint(ctx, f"INFO: Added server: {folder}")
                new_servers_found = True

        if not new_servers_found:
            await backend.send_msg("No new servers found.")
        else:
            await ctx.invoke(self.bot.get_command('serverselect'))  # Shows all servers in Discord embed

    # ===== Version
    @commands.command(aliases=['lversion', 'lver', 'lv', 'checklatest', 'checkupdate'])
    async def latestversion(self, ctx):
        """Gets latest Minecraft server version number from official website."""

        await ctx.send("***Fetching latest vanilla server version...***")
        version = await backend.server_api.check_latest_version()
        await backend.send_msg(f"Latest version: `{version}`")
        lprint(ctx, f"Fetched latest Minecraft server version: {version}")

    @commands.command(aliases=['updateserver', 'su', 'update'])
    async def serverupdate(self, ctx, now=''):
        """
        Updates server.jar file by downloading latest from official Minecraft website.

        Args:
            now optional: Stops server immediately without giving online players 15s warning.

        Usage:
            ?serverupdate
            ?su now

        Note: This will not make a backup beforehand, suggest doing so with ?serverbackup command.
        """

        lprint(ctx, f"Updating {config.get_config('server_name')}...")
        await backend.send_msg(f"***Updating {config.get_config('server_name')}...*** :arrows_counterclockwise:")

        # Halts server if running.
        if await backend.server_status() is not False:
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)
        await asyncio.sleep(5)

        await backend.send_msg(f"***Downloading latest server jar...***")
        url, version = await backend.server_api.server_update()  # Updates server.jar file.
        if version:
            await backend.send_msg(f"Version: `{version}`\nSource: `{url}`\nNOTE: Next launch may take longer than usual.")
            await asyncio.sleep(3)
        else: await backend.send_msg("**ERROR:** Updating server failed. Possible incompatibility.\nSuggest restoring from a backup if updating corrupted any files.")
        lprint(ctx, "Server Updated")

    # ===== Save/Autosave
    @commands.command(aliases=['sa', 'save-all'])
    async def saveall(self, ctx):
        """Save current world using server save-all command."""

        if await backend.send_command('save-all') is False: return

        await backend.send_msg("World Saved  :floppy_disk:")
        await backend.send_msg("**NOTE:** This is not the same as making a backup using `?backup`.")
        lprint(ctx, "Saved World")

    @commands.command()
    async def autosaveon(self, ctx):
        """Enables autosave."""

        await ctx.invoke(self.bot.get_command('autosave'), arg='on')

    @commands.command()
    async def autosaveoff(self, ctx):
        """Disables autosave."""

        await ctx.invoke(self.bot.get_command('autosave'), arg='off')

    @commands.command(aliases=['asave'])
    async def autosave(self, ctx, arg=''):
        """
        Sends save-all command at interval of x minutes.

        Args:
            arg optional: turn on/off autosave, or set interval in minutes.

        Usage:
            ?autosave - Shows current state
            ?autosave on
            ?autosave 60 - will send 'save-all' command to server every 60min.
        """

        if not arg: await backend.send_msg(f"Usage: Update interval(min) `?autosave 60`, activate `?autosave on`.")

        # Parses user input and sets invertal for autosave.
        try: arg = int(arg)
        except: pass
        else:
            config.set_config('autosave_interval', arg)

        # Enables/disables autosave tasks.loop(). Also edits slime_config.py file, so autosave state can be saved on bot restarts.
        arg = str(arg)
        if arg.lower() in utils.enable_inputs:
            if config.get_config('enable_autosave'):
                await backend.send_msg('Autosave already enabled')
                return
            # Starts loop, updates enable_autosave, edits slime_config.py, output to log
            self.autosave_task.start()
            config.set_config('enable_autosave', True)
            lprint(ctx, f"Autosave: Enabled (interval: {config.get_config('autosave_interval')}m)")
        elif arg.lower() in utils.disable_inputs:
            self.autosave_task.cancel()
            config.set_config('enable_autosave', False)
            lprint(ctx, 'Autosave: Disabled')

        status_msg = ':red_circle: **DISABLED** '
        if await backend.server_status() is False: status_msg = ":pause_button: **PAUSED**"
        elif config.get_config('enable_autosave'): status_msg = ':green_circle: **ENABLED**'

        fields = [['Status', f"{status_msg} | **{config.get_config('autosave_interval')}**min"],
                  ['Note', 'Auto save pauses if server unreachable (not same as disabled). Update server status with `?check` or `?stats`.']]
        await backend.send_msg(embed=comps.new_embed(fields, 'Autosave :repeat::floppy_disk:'))
        lprint(ctx, 'Fetched autosave information')

    @tasks.loop(seconds=config.get_config('autosave_interval') * 60)
    async def autosave_task(self):
        """Automatically sends save-all command to server at interval of x minutes."""

        await self.bot.wait_until_ready()
        # Will only send command if server is active. use ?check or ?stats to update server_active boolean so this can work.
        if await backend.send_command('save-all'):
            lprint(f"Autosaved (interval: {config.get_config('autosave_interval')}m)")

    # ===== Status/Info
    @commands.command(aliases=['pingserver', 'ping'])
    async def serverping(self, ctx):
        """Uses ping command to see if server_address is reachable."""

        await backend.send_msg('***Pinging Server...***')
        try: ping = f"({float(await backend.server_ping())}ms)"
        except: ping = ''
        if ping:
            await backend.send_msg(ping)
        else: await backend.send_msg("Unable to get ping.")

    @commands.command(aliases=['queryserver', 'pingquery', 'queryping', 'query'])
    async def serverquery(self, ctx):
        """
        Uses mctools library to get basic server info from server query.
        NOTE: Must have enable-query=true in server.properties for this to work.
        """

        await backend.send_msg("***Attempting Server Query...***")
        if response := await backend.server_ping_query():
            # Formats data to look nicer with indents, and also removes any unwanted escape characters.
            await backend.send_msg(f'```json\n{utils.remove_ansi(utils.print_dict_data(response)).strip()}```')
        else:
            await backend.send_msg("**ERROR:** Query ping failed.")

    @commands.command(aliases=['check', 'checkstatus', 'statuscheck', 'active', 'refresh'])
    async def servercheck(self, ctx):
        """Checks if server is online."""

        await backend.send_msg('***Checking Server Status...***')
        response = await backend.server_status()
        if response:
            await backend.send_msg("**Server ACTIVE** :green_circle:")
        elif response is None:
            await backend.send_msg("**ERROR:** Unable to check server status.")
        else: await backend.send_msg("**Server INACTIVE** :red_circle:")

    @commands.command(aliases=['stat', 'stats', 'status', 'info'])
    async def serverstatus(self, ctx):
        """Shows server active status, version, motd, and online players"""

        sstatus = await backend.server_status()
        if sstatus: status = '**ACTIVE** :green_circle:'
        elif sstatus is False: status = '**INACTIVE** :red_circle:'
        else: status = 'N/A'
        fields = [
            ['Current Server', f"Status: {status}\nServer: {config.get_config('server_name')}\nDescription: {config.get_config('server_description')}\nVersion: {await backend.get_server_version(force_check=True)}\nMOTD: {await backend.get_motd()}"],
            ['Autosave', f"{'Enabled' if config.get_config('enable_autosave') else 'Disabled'} ({config.get_config('autosave_interval')}min)"],
            ['Address', f"Address: ||`{config.get_config('server_address')}:{config.get_config('server_part')}`|| ({'Working' if await backend.server_ping() else 'Broken'})\nIP: ||`{utils.get_public_ip()}`|| (Use if Address broken))"],
            ['Location', f"`{config.get_config('server_path')}`"],
            ['Launch Command', f"`{config.get_config('server_launch_command')}`"]
        ]
        await backend.send_msg(embed=comps.new_embed(fields, 'Server Status'))

        if status is not False:  # Only fetches players list if server online.
            await ctx.invoke(self.bot.get_command('players'))
        await ctx.invoke(self.bot.get_command('bannermsg'))
        lprint(ctx, "Fetched server status")

    @commands.command(aliases=['log', 'mlog', 'slog'])
    async def serverlog(self, ctx, lines=20, match=None):
        """
        Show server log.

        Args:
            lines optional default(5): How many latest lines to show or how many matches to show if using 'match' argument.
            match optional: Filter lines, only show lines containing this. Must provide lines argument if using this one.

        Usage:
            ?serverlog - Defaults ot showing 5 lines
            ?log 10
            ?log 10 my coordinates - Gets 10 most recent lines containing 'my coordinates'.

        Note: When using the match argument, like '?log 5 hello', this doesn't mean it'll get the latest 5 lines and check
        if those lines contains 'hello'. Instead, it'll keep going through 'latest.log' until it finds 5 matches (or until the file ends).
        """

        await backend.send_msg(f"***Fetching {lines} Minecraft Log...*** :tools:")
        log_data = await backend.read_server_log(search=match, lines=lines, find_all=True)
        if log_data:
            await backend.send_msg(file=discord.File(utils.convert_to_bytes('\n'.join(log_data)), 'server.log'))
            lprint(ctx, f"Fetched Minecraft Log: {lines}")
        else:
            await backend.send_msg("**Error:** Problem fetching data.")
            lprint(ctx, "ERROR: Issue getting minecraft log data")

    @commands.command(aliases=['sclog', 'connectionlog', 'connectionslog', 'conlog', 'joinlog', 'loginlog'])
    async def serverconnectionslog(self, ctx, lines=20):
        """
        Shows log lines relating to connections (joining, disconnects, kicks, etc).

        Args:
            lines optional default(5): Number of lines to show.

        Usage:
            ?clogs - Shows recent 5 lines
            ?clogs 10
        """

        await backend.send_msg(f"***Fetching {lines} Connection Log...*** :satellite:")

        match_list = ['joined the game', 'logged in with entity id', 'left the game', 'lost connection:', 'Kicked by an operator', ]
        # Get only log lines that are connection related.
        log_data = await backend.read_server_log(search=match_list, lines=lines, find_all=True)
        if not log_data:
            await backend.send_msg("**ERROR:** Could not get chat log.")
            lprint(ctx, "ERROR: Problem fetching connections log.")
            return

        await backend.send_msg(file=discord.File(utils.convert_to_bytes('\n'.join(log_data)), 'connections_log.log'))
        lprint(ctx, f"Fetched Connection Log: {lines}")

    @commands.command(aliases=['minecraftversion', 'mversion', 'version'])
    async def serverversion(self, ctx):
        """Gets Minecraft server version."""

        response = await backend.get_server_version(force_check=True)
        if response is False:
            await backend.send_msg("**ERROR:** Could not get server version")
            lprint("ERROR: Couldn't get server version.")
            return
        await backend.send_msg(f"Current version: `{response}`")
        lprint(ctx, f"Fetched Minecraft server version: {response}")

    # === Properties
    @commands.command(aliases=['property', 'pr'])
    async def properties(self, ctx, target_property='', *value):
        """
        Check or change a server.properties property. May require restart.

        Args:
            target_property: Target property to change, must be exact in casing and spelling and some may include a dash -.
            value optional: New value. For some properties you will need to input a lowercase true or false, and for others you may input a string (quotes not needed).

        Usage:
            ?property motd - Shows current value for 'motd'
            ?pr spawn-protection 2 - Updates 'spawn-protection' value to 2
            ?property all, ?pa - Shows all properties.

        Note: Passing in 'all' for target property argument (with nothing for value argument) will show all the properties.
        """

        if not target_property:
            await backend.send_msg("Usage: `?property <property_name> [new_value]`\nExample: `?property motd`, `?p motd Hello World!`\n"
                           "Show all properties using `?properties all` or `?pa`")
            return False

        # Parse value from *value tuple.
        value = utils.get_parameter(value)

        if 'all' in target_property:
            await ctx.invoke(self.bot.get_command('propertiesall'))

        if server_property := await backend.get_property(target_property):

            # Update server property
            if value:
                if updated_property := await backend.update_property(target_property, value):
                    await backend.send_msg(f"Property Updated: `{updated_property}`")
                    return
                else:
                    await backend.send_msg(f"**ERROR:** Could not update server property: `{target_property}` to `{value}`")
                    return False

            # Return current property value
            await backend.send_msg(f"Server property: `{server_property}`")
            lprint(ctx, f"Server property: {server_property}")
            return

        # If property not found.
        await backend.send_msg(f"**ERROR:** Server property not found: {target_property}")
        return False

    @commands.command(aliases=['pa', 'prall'])
    async def propertiesall(self, ctx):
        """Shows full server properties file."""

        if not isfile(config.get_config('server_properties_filepath')):
            await backend.send_msg('**ERROR:** Could not get server properties file')
            return
        with open(config.get_config('server_properties_filepath'), 'rb') as f:
            await backend.send_msg(file=discord.File(f, config.get_config('server_properties_filepath')))

        #await ctx.invoke(self.bot.get_command('properties'), target_property='all')

    @commands.command(aliases=['serveronlinemode', 'omode', 'om'])
    async def onlinemode(self, ctx, mode=''):
        """
        Check or enable/disable onlinemode property. Restart required.

        Args:
            mode optional: Update onlinemode property in server.properties file. Must be in lowercase.

        Usage:
            ?onlinemode - Shows current state
            ?onlinemode true
            ?omode false
        """

        if not mode:
            online_mode = backend.edit_file('online-mode')[1]
            await backend.send_msg(f"online mode: `{online_mode}`")
            lprint(ctx, f"Fetched online-mode state: {online_mode}")
        elif mode in ['true', 'false']:
            backend.edit_file('online-mode', mode)
            server_property = backend.edit_file('online-mode')
            await backend.send_msg(f"Updated online mode: `{server_property[1]}`")
            await backend.send_msg("**Note:** Server restart required for change to take effect.")
            lprint(ctx, f"Updated online-mode: {server_property[1].strip()}")
        else: await backend.send_msg("Need a true or false argument (in lowercase).")

    @commands.command(aliases=['updatemotd', 'servermotd'])
    async def motd(self, ctx, *message):
        """
        Check or Update motd property. Restart required.

        Args:
            message optional: New message for message of the day for server. No quotes needed.

        Usage:
            ?motd - Shows current message set.
            ?motd YAGA YEWY!
        """

        message = utils.format_args(message)
        if message:
            if await backend.update_property('motd', message):
                await backend.send_msg(f"Updated MOTD: `{message}`")
                lprint(ctx, f"Updated MOTD: {message}")
            else:
                await backend.send_msg('**ERROR:** Problem updating motd.')

        elif current_motd := await backend.get_motd():
            await backend.send_msg(f"Current MOTD: `{current_motd}`")
            lprint(ctx, f"Fetched MOTD: {current_motd}")
        else:
            await backend.send_msg('**Error:** Fetching server motd failed.')

    @commands.command(aliases=['serverrcon'])
    async def rcon(self, ctx, state=''):
        """
        Check RCON status, enable/disable enable-rcon property. Restart required.

        Args:
            state: Set enable-rcon property in server.properties file, true or false must be in lowercase.

        Usage:
            ?rcon
            ?rcon true
            ?rcon false
        """

        if state in ['true', 'false', '']:
            response = backend.edit_file('enable-rcon', state)
            await backend.send_msg(f"`{response[0]}`")
        else: await backend.send_msg("Need a true or false argument (in lowercase).")

    # ===== Start/Stop
    @commands.command(aliases=['startserver', 'start'])
    async def serverstart(self, ctx):
        """
        Start Minecraft server.

        Note: Depending on your system, server may take 15 to 40+ seconds to fully boot.
        """

        # Exits function if server already online.
        if await backend.server_status():
            await backend.send_msg("**Server ACTIVE** :green_circle:")
            return False

        if not await backend.server_api.server_start():
            await backend.send_msg("**Error:** Could not start Minecraft server.")
            return False
        await backend.send_msg(f"***Launching Minecraft Server...*** :rocket:\nServer Selected: **{config.get_config('server_name')}**\nStartup time: {config.get_config('startup_wait_time')}s.")

        # checks if set custom wait time in selected_server list.
        try: wait_time = int(config.server_configs['startup_wait_time'])
        except: wait_time = config.get_config('startup_wait_time')
        await backend.send_msg(f"***Fetching Status in {wait_time}s...***")
        await asyncio.sleep(wait_time)

        await ctx.invoke(self.bot.get_command('serverstatus'))
        lprint(ctx, "Starting Minecraft Server")

    @commands.command(aliases=['stopserver', 'stop'])
    async def serverstop(self, ctx, now=''):
        """
        Stop Minecraft server, gives players 15s warning.

        Args:
            now optional: Stops server immediately without giving online players 15s warning.

        Usage:
            ?stop
            ?stop now
        """

        if await backend.server_status() is False:
            await backend.send_msg("Already Offline")
            return

        await backend.send_msg("***Stopping Minecraft Server...***")
        if 'now' in now:
            await backend.send_command('save-all')
            await asyncio.sleep(3)
            await backend.server_api.server_stop()
        else:
            await backend.send_command('say ---WARNING--- Server will halt in 15s!')
            await backend.send_msg("***Halting Minecraft Server in 15s...***")
            await asyncio.sleep(10)
            await backend.send_command('say ---WARNING--- 5s left!')
            await asyncio.sleep(5)
            await backend.send_command('save-all')
            await asyncio.sleep(3)

            await backend.server_api.server_stop()

        await asyncio.sleep(1)
        await backend.send_msg("**Halted Minecraft Server** :stop_sign:")
        lprint(ctx, "Stopping Server")

    @commands.command(aliases=['restartserver', 'restart'])
    async def serverrestart(self, ctx, now=''):
        """
        Restarts server with 15s warning to players.

        Args:
            now optional: Restarts server immediately without giving online players 15s warning.

        Usage:
            ?restart
            ?reboot now
        """

        await backend.send_command('say ---WARNING--- Server Rebooting...')
        lprint(ctx, "Restarting Server")
        await backend.send_msg("***Restarting Minecraft Server...*** :repeat:")
        await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await asyncio.sleep(3)
        await ctx.invoke(self.bot.get_command('serverstart'))

async def setup(bot):
    await bot.add_cog(Server(bot))
