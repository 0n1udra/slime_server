import discord, asyncio
from discord.ext import commands, tasks
from bot_files.backend_functions import send_command, format_args, server_status, lprint
import bot_files.backend_functions as backend
import bot_files.components as components
import slime_vars

ctx = 'slime_bot.py'
# ========== Server: autosave, Start/stop, Status, edit property, backup/restore.
class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if slime_vars.autosave_status is True:
            self.autosave_loop.start()
            lprint(ctx, f"Autosave task started (interval: {slime_vars.autosave_interval}m)")

    @commands.command(aliases=['sselect', 'serversselect', 'serverslist', 'ss'])
    async def serverlist(self, ctx, *name):
        """
        Select server to use all other commands on. Each server has their own world_backups and server_restore folders.

        Args:
            name: name of server to select, use ?selectserver list or without arguments to show list.

        Usage:
            ?selectserver list
            ?selectserver papermc
        """

        if 'button' in name:
            name = components.data('second_selected')
            if not name: return
        else: name = format_args(name)
        if not name or 'list' in name:
            embed = discord.Embed(title='Server List :desktop:')
            for server in slime_vars.server_list.values():
                # Shows server name, description, location, and start command.
                embed.add_field(name=server[0], value=f"Description: {server[1]}\nLocation: `{slime_vars.mc_path}/{slime_vars.server_selected[0]}`\nStart Command: `{server[2]}`", inline=False)
            await ctx.send(embed=embed)
            await ctx.send(f"**Current Server:** `{slime_vars.server_selected[0]}`")
            await ctx.send(f"Use `?serverselect` to list, or `?ss [server]` to switch.")
        elif name in slime_vars.server_list:
            backend.server_selected = slime_vars.server_list[name]
            backend.server_path = f"{slime_vars.mc_path}/{slime_vars.server_selected[0]}"
            backend.edit_file('server_selected', f" server_list['{name}']", slime_vars.slime_vars_file)
            await ctx.invoke(self.bot.get_command('botrestart'))
        else: await ctx.send("**ERROR:** Server not found.")

    @commands.command(aliases=['si'])
    async def serverinfo(self, ctx):
        await ctx.send("Coming soon.")

    @commands.command(hidden=True)
    async def servernew(self, ctx, interaction):
        await ctx.send("Coming soon")
        return
        if interaction == 'submitted':
            data = components.data('servernew')
            fields = [['Name', data['name']], ['Description', data['description']], ['Start Command', f"`{data['command']}`"], ['Wait Time', data['wait']]]
            await ctx.send(embed=components.new_embed(fields, 'New Server'))
            await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')

        else:
            modal_fields = [['text', 'Server Name', 'name', 'Name of new server', None, False, True, 50],  # type (text, select), label, custom_id, placeholder, default, style(True=long), required, max length
                            ['text', 'Description', 'description', 'Add description', None, True, False, 500],
                            ['text', 'Start Command', 'command', 'Runtime start command for .jar file', f'java {slime_vars.java_params} -jar server.jar nogui', True, True, 500],
                            ['text', 'Wait Time', 'wait', 'After starting server, bot will wait before fetching server status and other info.', 30, True, False, 500]]
            modal_msg = await interaction.response.send_modal(components.new_modal(modal_fields, 'New Server', 'servernew'))

    @commands.command(aliases=['sc'])
    async def servercopy(self, ctx, server=''):
        await ctx.send("Coming soon.")

    @commands.command(hidden=True)
    async def serveredit(self, ctx):
        await ctx.send("Coming soon.")

    @commands.command(hidden=True)
    async def serverdelete(self, ctx):
        await ctx.send("Coming Soon")
        return
        """
        Delete a server

        Args:
            server: I
        """

        to_delete = f"{slime_vars.servers_path}/{components.data('second_selected', reset=True)}"
        try: backend.delete_dir(to_delete)
        except:
            await ctx.send(f"**Error:** Issue deleting server: `{to_delete}`")
            return False

        await ctx.send(f"**Server Deleted:** `{to_delete}`")
        lprint(ctx, "Deleted server: " + to_delete)

        try: await ctx.invoke(self.bot.get_command('_update_control_panel'), 'servers')
        except: pass

    # ===== Version
    @commands.command(aliases=['lversion', 'lver', 'lv'])
    async def latestversion(self, ctx):
        """Gets latest Minecraft server version number from official website."""

        response = backend.check_latest()
        await ctx.send(f"Latest version: `{response}`")
        lprint(ctx, "Fetched latest Minecraft server version: " + response)

    @commands.command(aliases=['updateserver', 'su'])
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

        if slime_vars.server_selected[0] in slime_vars.updatable_mc:
            lprint(ctx, f"Updating {slime_vars.server_selected[0]}...")
            await ctx.send(f"***Updating {slime_vars.server_selected[0]}...*** :arrows_counterclockwise:")
        else:
            await ctx.send(f"**ERROR:** This command is not compatible with you're server variant.\n`{slime_vars.server_selected[0]}` currently selected.")
            return False

        # Halts server if running.
        if await server_status():
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)
        await asyncio.sleep(5)

        await ctx.send(f"***Downloading latest server jar***\nFrom: `{slime_vars.server_selected[3]}`")
        server = backend.download_latest()  # Updates server.jar file.
        if server:
            await ctx.send(f"Downloaded latest version: `{server}`\nNext launch may take longer than usual.")
            await asyncio.sleep(3)
        else: await ctx.send("**ERROR:** Updating server failed. Suggest restoring from a backup if updating corrupted any files.")
        lprint(ctx, "Server Updated")

    # ===== Save/Autosave
    @commands.command(aliases=['sa', 'save-all'])
    async def saveall(self, ctx):
        """Save current world using server save-all command."""

        if not await send_command('save-all'): return

        await ctx.send("World Saved  :floppy_disk:")
        await ctx.send("**NOTE:** This is not the same as making a backup using `?backup`.")
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

        if not arg: await ctx.send(f"Usage: Update interval(min) `?autosave 60`, activate `?autosave on`.")

        # Parses user input and sets invertal for autosave.
        try: arg = int(arg)
        except: pass
        else:
            slime_vars.autosave_interval = arg
            backend.edit_file('autosave_interval', f" {arg}", slime_vars.slime_vars_file)

        # Enables/disables autosave tasks.loop(). Also edits slime_vars.py file, so autosave state can be saved on bot restarts.
        arg = str(arg)
        if arg.lower() in backend.enable_inputs:
            # Starts loop, updates autosave_status, edits slime_vars.py, output to log
            self.autosave_loop.start()
            slime_vars.autosave_status = True
            backend.edit_file('autosave_status', ' True', slime_vars.slime_vars_file)
            lprint(ctx, f'Autosave: Enabled (interval: {slime_vars.autosave_interval}m)')
        elif arg.lower() in backend.disable_inputs:
            self.autosave_loop.cancel()
            slime_vars.autosave_status = False
            backend.edit_file('autosave_status', ' False', slime_vars.slime_vars_file)
            lprint(ctx, 'Autosave: Disabled')

        status_msg = ':red_circle: **DISABLED** '
        if not await server_status(discord_msg=False): status_msg = ":pause_button: **PAUSED**"
        elif slime_vars.autosave_status: status_msg = ':green_circle: **ENABLED**'

        fields = [['Status', f"{status_msg} | **{slime_vars.autosave_interval}**min"],
                  ['Note', 'Auto save pauses if server unreachable (not same as disabled). Update server status with `?check` or `?stats`.']]
        await ctx.send(embed=components.new_embed(fields, 'Autosave :repeat::floppy_disk:'))
        lprint(ctx, 'Fetched autosave information')

    @tasks.loop(seconds=slime_vars.autosave_interval * 60)
    async def autosave_loop(self):
        """Automatically sends save-all command to server at interval of x minutes."""

        # Will only send command if server is active. use ?check or ?stats to update server_active boolean so this can work.
        if await send_command('save-all', discord_msg=False):
            lprint(ctx, f"Autosaved (interval: {slime_vars.autosave_interval}m)")

    @autosave_loop.before_loop
    async def before_autosaveall_loop(self):
        """Makes sure bot is ready before autosave_loop can be used."""

        await self.bot.wait_until_ready()

    # ===== Status/Info
    @commands.command(aliases=['check', 'checkstatus', 'statuscheck', 'active', 'refresh'])
    async def servercheck(self, ctx, show_msg=True):
        """Checks if server is online."""

        await ctx.send('***Checking Server Status...***')
        await server_status(discord_msg=show_msg)

    @commands.command(aliases=['stat', 'stats', 'status', 'info'])
    async def serverstatus(self, ctx):
        """Shows server active status, version, motd, and online players"""

        fields = [['Current Server', f"Status: {'**ACTIVE** :green_circle:' if await server_status() is True else '**INACTIVE** :red_circle:'}\n\
Server: {slime_vars.server_selected[0]}\nDescription: {slime_vars.server_selected[1]}\nVersion: {backend.server_version()}\nMOTD: {backend.server_motd()}"],
                  ['Autosave', f"{'Enabled' if slime_vars.autosave_status is True else 'Disabled'} ({slime_vars.autosave_interval}min)"],
                  ['Address', f"IP: ||`{backend.get_public_ip()}`||\nURL: ||`{slime_vars.server_url}`|| ({backend.ping_url()})"],
                  ['Location', f"`{slime_vars.server_path}`"],
                  ['Start Command', f"`{slime_vars.server_selected[2]}`"]]
        await ctx.send(embed=components.new_embed(fields, 'Server Status'))

        if await server_status():  # Only fetches players list if server online.
            await ctx.invoke(self.bot.get_command('players'))
        await ctx.invoke(self.bot.get_command('_control_panel_msg'))
        lprint(ctx, "Fetched server status")

    @commands.command(aliases=['log', 'mlog'])
    async def serverlog(self, ctx, lines=5, match=None):
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

        # If received match argument, switches server_log mode.
        filter_mode, log_mode = False, True
        if match: filter_mode, log_mode = True, False

        file_path = f"{slime_vars.server_path}/logs/latest.log"
        await ctx.send(f"***Fetching {lines} Minecraft Log...*** :tools:")
        log_data = backend.server_log(match=match, file_path=file_path, lines=lines, log_mode=log_mode, filter_mode=filter_mode, return_reversed=True)
        if log_data:
            i = 0
            for line in log_data.split('\n'):
                i += 1
                # E.g. '[16:28:28 INFO]: There are 1 of a max of 20 players online: R3diculous' >
                # '3: (16:28:28) [Server thread/INFO]: There are 1 of a max of 20 players online: R3diculous' (With Discord markdown)
                await ctx.send(f"**{i}**: _({line.split(']', 1)[0][1:]})_ `{line.split(']', 1)[-1][1:]}`")
            await ctx.send("-----END-----")
            lprint(ctx, f"Fetched Minecraft Log: {lines}")
        else:
            await ctx.send("**Error:** Problem fetching data.")
            lprint(ctx, "ERROR: Issue getting minecraft log data")

    @commands.command(aliases=['clog', 'clogs', 'connectionlog', 'connectionslog', 'serverconnectionlog', 'joinedlog', 'loginlog'])
    async def serverconnectionslog(self, ctx, lines=5):
        """
        Shows log lines relating to connections (joining, disconnects, kicks, etc).

        Args:
            lines optional default(5): Number of lines to show.

        Usage:
            ?clogs - Shows recent 5 lines
            ?clogs 10
        """

        await ctx.send(f"***Fetching {lines} Connection Log...*** :satellite:")

        match_list = ['joined the game', 'logged in with entity id', 'left the game', 'lost connection:', 'Kicked by an operator', ]
        # Get only log lines that are connection related.
        log_data = backend.server_log(match_list=match_list, lines=lines, filter_mode=True, return_reversed=True)
        try: log_data = log_data.strip().split('\n')
        except:
            await ctx.send("**ERROR:** Problem fetching connection logs, there may be nothing to fetch.")
            return False

        i = lines
        # Prints out log lines with Discord markdown.
        for line in log_data:
            if i <= 0: break
            i -= 1

            # Gets timestamp from start of line.
            timestamp = line.split(']', 1)[0][1:]
            # '[15:51:31 INFO]: R3diculous left the game' > ['R3diculous', 'left the game'] > '(16:30:36) R3diculous: joined the gameA'
            line = line.split(']:', 1)[-1][1:].split(' ', 1)
            # Extracts wanted data and formats it into a Discord message with markdown.
            line = f"_({timestamp})_ **{line[0]}**: {line[1]}"
            await ctx.send(f'{line}')

        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched Connection Log: {lines}")

    @commands.command(aliases=['minecraftversion', 'mversion'])
    async def serverversion(self, ctx):
        """Gets Minecraft server version."""

        response = backend.server_version()
        await ctx.send(f"Current version: `{response}`")
        lprint(ctx, "Fetched Minecraft server version: " + response)

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
            ?property spawn-protection 2 - Updates 'spawn-protection' value to 2
            ?property all - Shows all properties.

        Note: Passing in 'all' for target property argument (with nothing for value argument) will show all the properties.
        """

        if not target_property:
            await ctx.send("Usage: `?property <property_name> [new_value]`\nExample: `?property motd`, `?p motd Hello World!`")
            return False

        if value:
            await ctx.send("Property Updated  :memo:")
            value = ' '.join(value)
        else: value = ''

        backend.edit_file(target_property, value)
        fetched_property = backend.edit_file(target_property)
        await asyncio.sleep(2)

        if fetched_property:
            await ctx.send(f"`{fetched_property[0].strip()}`")
            lprint(ctx, f"Server property: {fetched_property[0].strip()}")
        else:
            await ctx.send(f"**ERROR:** 404 Property not found.")
            lprint(ctx, f"Server property not found: {target_property}")

    @commands.command()
    async def propertiesall(self, ctx):
        """Shows full server properties file."""

        await ctx.invoke(self.bot.get_command('properties'), target_property='all')

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
            await ctx.send(f"online mode: `{online_mode}`")
            lprint(ctx, f"Fetched online-mode state: {online_mode}")
        elif mode in ['true', 'false']:
            backend.edit_file('online-mode', mode)
            server_property = backend.edit_file('online-mode')
            await ctx.send(f"Updated online mode: `{server_property[1]}`")
            await ctx.send("**Note:** Server restart required for change to take effect.")
            lprint(ctx, f"Updated online-mode: {server_property[1].strip()}")
        else: await ctx.send("Need a true or false argument (in lowercase).")

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

        message = format_args(message)

        if slime_vars.use_rcon:
            motd_property = backend.server_motd()
        elif slime_vars.server_files_access:
            backend.edit_file('motd', message)
            motd_property = backend.edit_file('motd')
        else: motd_property = '**ERROR:** Fetching server motd failed.'

        if message:
            await ctx.send(f"Updated MOTD: `{motd_property[0].strip()}`")
            lprint(ctx, "Updated MOTD: " + motd_property[1].strip())
        else:
            await ctx.send(f"Current MOTD: `{motd_property[1]}`")
            lprint(ctx, "Fetched MOTD: " + motd_property[1].strip())

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
            await ctx.send(f"`{response[0]}`")
        else: await ctx.send("Need a true or false argument (in lowercase).")

    # ===== Start/Stop
    @commands.command(aliases=['startminecraft', 'mstart'])
    async def serverstart(self, ctx):
        """
        Start Minecraft server.

        Note: Depending on your system, server may take 15 to 40+ seconds to fully boot.
        """

        # Exits function if server already online.
        if await server_status():
            await ctx.send("**Server ACTIVE** :green_circle:")
            return False

        await ctx.send(f"***Launching Minecraft Server...*** :rocket:\nAddress: `{slime_vars.server_url}`\nPlease wait about 15s before attempting to connect.")
        backend.server_start()

        # checks if set custom wait time in server_selected list.
        try: wait_time = int(slime_vars.server_selected[-1])
        except: wait_time = slime_vars.default_wait_time
        await ctx.send(f"***Fetching Status in {wait_time}s...***")
        await asyncio.sleep(wait_time)

        await ctx.invoke(self.bot.get_command('serverstatus'))
        lprint(ctx, "Starting Minecraft Server")

    @commands.command(aliases=['minecraftstop', 'stopminecraft', 'mstop'])
    async def serverstop(self, ctx, now=''):
        """
        Stop Minecraft server, gives players 15s warning.

        Args:
            now optional: Stops server immediately without giving online players 15s warning.

        Usage:
            ?stop
            ?stop now
        """

        if not await server_status():
            await ctx.send("Already Offline")
            return

        await ctx.send("***Stopping Minecraft Server...***")
        if 'now' in now:
            await send_command('save-all')
            await asyncio.sleep(3)
            await send_command('stop')
        else:
            await send_command('say ---WARNING--- Server will halt in 15s!')
            await ctx.send("***Halting Minecraft Server in 15s...***")
            await asyncio.sleep(10)
            await send_command('say ---WARNING--- 5s left!')
            await asyncio.sleep(5)
            await send_command('save-all')
            await asyncio.sleep(3)
            await send_command('stop')

        await asyncio.sleep(5)
        await ctx.send("**Halted Minecraft Server** :stop_sign:")
        backend.mc_subprocess = None
        lprint(ctx, "Stopping Server")

    @commands.command(aliases=['rebootserver', 'restartserver', 'serverreboot', 'mrestart'])
    async def serverrestart(self, ctx, now=''):
        """
        Restarts server with 15s warning to players.

        Args:
            now optional: Restarts server immediately without giving online players 15s warning.

        Usage:
            ?restart
            ?reboot now
        """

        await send_command('say ---WARNING--- Server Rebooting...')
        lprint(ctx, "Restarting Server")
        await ctx.send("***Restarting Minecraft Server...*** :repeat:")
        await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await asyncio.sleep(3)
        await ctx.invoke(self.bot.get_command('serverstart'))

async def setup(bot):
    await bot.add_cog(Server(bot))
