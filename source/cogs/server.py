import discord, asyncio
from discord.ext import commands, tasks
from bot_files.backend_functions import server_command, format_args, server_status, lprint
import bot_files.backend_functions as backend
import slime_vars

ctx = 'slime_bot.py'

# ========== Basics: Say, whisper, online players, server command pass through.
class Basics(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['mcommand', 'm/'])
    async def servercommand(self, ctx, *command):
        """
        Pass command directly to server.

        Args:
            command: Server command, do not include the slash /.

        Usage:
            ?mcommand broadcast Hello Everyone!
            ?m/ toggledownfall

        Note: You will get the latest 2 lines from server output, if you need more use ?log.
        """

        command = format_args(command)
        if not await server_command(command): return False

        lprint(ctx, "Sent command: " + command)
        await ctx.invoke(self.bot.get_command('serverlog'), lines=3)

    @commands.command(aliases=['broadcast', 's'])
    async def say(self, ctx, *msg):
        """
        sends message to all online players.

        Args:
            msg: Message to broadcast.

        Usage:
            ?s Hello World!
        """

        msg = format_args(msg)

        if not msg:
            await ctx.send("Usage: `?s <message>`\nExample: `?s Hello everyone!`")
        else:
            if await server_command('say ' + msg):
                await ctx.send("Message circulated to all active players :loudspeaker:")
                lprint(ctx, f"Server said: {msg}")

    @commands.command(aliases=['whisper', 't', 'w'])
    async def tell(self, ctx, player='', *msg):
        """
        Message online player directly.

        Args:
            player: Player name, casing does not matter.
            msg optional: The message, no need for quotes.

        Usage:
            ?tell Steve Hello there!
            ?t Jesse Do you have diamonds?
        """

        msg = format_args(msg)
        if not player or not msg:
            await ctx.send("Usage: `?tell <player> <message>`\nExample: `?ttell MysticFrogo sup hundo`")
            return False

        if not await server_command(f"tell {player} {msg}"): return

        await ctx.send(f"Communiqué transmitted to: `{player}` :mailbox_with_mail:")
        lprint(ctx, f"Messaged {player} : {msg}")

    @commands.command(aliases=['chat', 'playerchat', 'getchat', 'showchat'])
    async def chatlog(self, ctx, *args):
        """
        Shows chat log. Does not include whispers.

        Args:
            lines optional default(5): How many log lines to look through. This is not how many chat lines to show.

        Usage:
            ?chat - Shows latest 5 player chat lines from log file.
            ?chat 50 - May take a while to load all 50 lines.
        """

        try:
            lines = int(args[0])
            args = args[1:]
        except: lines = 5

        try: keyword = ' ' .join(args)
        except: keyword = None

        await ctx.send(f"***Loading {lines} Chat Log...*** :speech_left:")

        # Get only log lines that are user chats.
        log_data = backend.server_log(']: <', lines=lines, filter_mode=True, return_reversed=True)

        try: log_data = log_data.strip().split('\n')
        except:
            await ctx.send("**ERROR:** Problem fetching chat logs, there may be nothing to fetch.")
            return False

        # optionally filter out chat lines only with certain keywords.
        log_data = [i for i in log_data if keyword.lower() in i.lower()]

        i = lines
        for line in log_data:
            # Only show specified number of lines from 'lines' parameter.
            if i <= 0: break
            i -= 1

            # Extracts wanted data from log line and formats it in Discord markdown.
            # '[15:26:49 INFO]: <R3diculous> test' > '(15:26:49) R3diculous: test' (With Discord markdown)
            timestamp = line.split(']', 1)[0][1:]
            line = line.split(']: <', 1)[-1].split('>', 1)
            await ctx.send(f"_({timestamp})_ **{line[0]}**: {line[-1][1:]}")

        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched Chat Log: {lines}")

# ========== World: weather, time.
class World(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Weather
    @commands.command(aliases=['weather', 'setweather'])
    async def weatherset(self, ctx, state='', duration=0):
        """
        Set weather.

        Args:
            state: <clear/rain/thunder>: Weather to change to.
            duration optional default(0): Duration in seconds. 0 means random duration.

        Usage:
            ?weatherset rain - Rain for random duration.
            ?weather thunder 60
        """

        if not state:
            await ctx.send("Usage: `?weather <state> [duration]`\nExample: `?weather rain`")
            return False

        if not await server_command(f'weather {state} {duration}'): return

        await ctx.send(f"Weather set to: **{state.capitalize()}** {'(' + str(duration) + 's)' if duration else ''}")
        lprint(ctx, f"Weather set to: {state.capitalize()} for {duration}s")

    @commands.command(aliases=['enableweather', 'weatherenable'])
    async def weatheron(self, ctx):
        """Enable weather cycle."""

        await server_command(f'gamerule doWeatherCycle true')
        await ctx.send("Weather cycle **ENABLED**")
        lprint(ctx, 'Weather Cycle: Enabled')

    @commands.command(aliases=['disableweather', 'weatherdisable'])
    async def weatheroff(self, ctx):
        """Disable weather cycle."""

        await server_command(f'gamerule doWeatherCycle false')
        await ctx.send("Weather cycle **DISABLED**")
        lprint(ctx, 'Weather Cycle: Disabled')

    @commands.command(aliases=['clearweather', 'weathersetclear'])
    async def weatherclear(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='clear')
        lprint(ctx, 'Weather: Disabled')

    @commands.command(aliases=['rainweather', 'weathersetrain'])
    async def weatherrain(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='rain')
        lprint(ctx, 'Weather: Disabled')

    @commands.command(aliases=['thunderweather', 'weathersetthunder'])
    async def weatherthunder(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='thunder')
        lprint(ctx, 'Weather: Disabled')

    # ===== Time
    @commands.command(aliases=['time', 'settime'])
    async def timeset(self, ctx, set_time=''):
        """
        Set time.

        Args:
            set_time: Set time either using day|night|noon|midnight or numerically.

        Usage:
            ?timeset day
            ?time 12
        """

        if set_time:
            if not await server_command(f"time set {set_time}"): return
            await ctx.send("Time Updated  :clock9:")
        else: await ctx.send("Need time input, like: `12`, `day`")
        lprint(ctx, f"Timed set: {set_time}")

    @commands.command(aliaases=['daytime', 'setday', 'timesetday'])
    async def timeday(self, ctx):
        """Set time to day."""

        await ctx.invoke(self.bot.get_command('timeset'), set_time='10000')

    @commands.command(aliases=['nighttime', 'setnight', 'timesetnight'])
    async def timenight(self, ctx):
        """Set time to night."""

        await ctx.invoke(self.bot.get_command('timeset'), set_time='14000')

    @commands.command(aliases=['enabletime', 'timecycleon'])
    async def timeon(self, ctx):
        """Enable day light cycle."""

        await server_command(f'gamerule doDaylightCycle true')
        await ctx.send("Daylight cycle **ENABLED**")
        lprint(ctx, 'Daylight Cycle: Enabled')

    @commands.command(aliases=['diabletime', 'timecycleoff'])
    async def timeoff(self, ctx):
        """Disable day light cycle."""

        await server_command(f'gamerule doDaylightCycle false')
        await ctx.send("Daylight cycle **DISABLED**")
        lprint(ctx, 'Daylight Cycle: Disabled')

# ========== Server: autosave, Start/stop, Status, edit property, backup/restore.
class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if slime_vars.autosave_status is True:
            #await self.autosave_loop.start()
            lprint(ctx, f"Autosave task started (interval: {slime_vars.autosave_interval}m)")

    # ===== Manage servers (not its backups)
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

        name = format_args(name)
        if not name or 'list' in name:
            embed = discord.Embed(title='Server List :desktop:')
            for server in slime_vars.server_list.values():
                # Shows server name, description, location, and start command.
                embed.add_field(name=server[0], value=f"Description: {server[1]}\nLocation: `{slime_vars.mc_path}/{slime_vars.server_selected[0]}`\nStart Command: `{server[2]}`", inline=False)
            await ctx.send(embed=embed)
            await ctx.send(f"**Current Server:** `{slime_vars.server_selected[0]}`")
            await ctx.send(f"Use `?serverselect` to list, or `?ss [server]` to switch.")
        elif name in slime_vars.server_list.keys():
            backend.server_selected = slime_vars.server_list[name]
            backend.server_path = f"{slime_vars.mc_path}/{slime_vars.server_selected[0]}"
            backend.edit_file('server_selected', f" server_list['{name}']", slime_vars.slime_vars_file)
            await ctx.invoke(self.bot.get_command('restartbot'))
        else: await ctx.send("**ERROR:** Server not found.")

    @commands.command(aliases=['newserver', 'createserver'])
    async def servercreate(self, ctx):
        class MyModal(discord.ui.Modal):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.add_item(discord.ui.TextInput(label="Short Input"))
                self.add_item(discord.ui.TextInput(label="Long Input", style=discord.TextStyle.long))

            async def callback(self, interaction: discord.Interaction):
                embed = discord.Embed(title="Modal Results")
                embed.add_field(name="Short Input", value=self.children[0].value)
                embed.add_field(name="Long Input", value=self.children[1].value)
                await interaction.response.send_message(embeds=[embed])

        modal = MyModal(title="Modal via Slash Command")
        await ctx.send(view=modal)

    # ===== Save/Autosave
    @commands.command(aliases=['sa', 'save-all'])
    async def saveall(self, ctx):
        """Save current world using server save-all command."""

        if not await server_command('save-all'): return

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

        if not arg: await ctx.send(f"Usage Examples: Update interval (minutes) `?autosave 60`, turn on `?autosave on`.")

        # Parses user input and sets invertal for autosave.
        try: arg = int(arg)
        except: pass
        else:
            slime_vars.autosave_interval = arg
            backend.edit_file('autosave_interval', f" {arg}", slime_vars.slime_vars_file)

        # Enables/disables autosave tasks.loop(). Also edits slime_vars.py file, so autosave state can be saved on bot restarts.
        arg = str(arg)
        if arg.lower() in backend.enable_inputs:
            slime_vars.autosave_status = True
            self.autosave_loop.start()
            backend.edit_file('autosave_status', ' True', slime_vars.slime_vars_file)
            lprint(ctx, f'Autosave: Enabled (interval: {slime_vars.autosave_interval}m)')
        elif arg.lower() in backend.disable_inputs:
            slime_vars.autosave_status = False
            self.autosave_loop.cancel()
            backend.edit_file('autosave_status', ' False', slime_vars.slime_vars_file)
            lprint(ctx, 'Autosave: Disabled')

        await ctx.send(f"Auto save function: {'**ENABLED** :repeat::floppy_disk:' if slime_vars.autosave_status else '**DISABLED**'}")
        await ctx.send(f"Auto save interval: **{slime_vars.autosave_interval}** minutes.")
        await ctx.send('**Note:** Auto save loop will pause(not same as disabled) when server is offline. If server is back online, use `?check` or `?stats` to update the bot.')
        lprint(ctx, 'Fetched autosave information')

    @tasks.loop(seconds=slime_vars.autosave_interval * 60)
    async def autosave_loop(self):
        """Automatically sends save-all command to server at interval of x minutes."""

        # Will only send command if server is active. use ?check or ?stats to update server_active boolean so this can work.
        if await server_command('save-all', discord_msg=False):
            lprint(ctx, f"Autosaved (interval: {slime_vars.autosave_interval}m)")

    @autosave_loop.before_loop
    async def before_autosaveall_loop(self):
        """Makes sure bot is ready before autosave_loop can be used."""

        await self.bot.wait_until_ready()

    # ===== Status/Info
    @commands.command(aliases=['check', 'checkstatus', 'statuscheck', 'active'])
    async def servercheck(self, ctx, show_msg=True):
        """Checks if server is online."""

        await ctx.send('***Checking Server Status...***')
        await server_status(discord_msg=show_msg)

    @commands.command(aliases=['stat', 'stats', 'status'])
    async def serverstatus(self, ctx):
        """Shows server active status, version, motd, and online players"""

        embed = discord.Embed(title='Server Status')
        embed.add_field(name='Current Server', value=f"Status: {'**ACTIVE** :green_circle:' if await server_status() is True else '**INACTIVE** :red_circle:'}\n\
            Server: {slime_vars.server_selected[0]}\nDescription: {slime_vars.server_selected[1]}\nVersion: {backend.server_version()}\n\
            MOTD: {backend.server_motd()}", inline=False)
        embed.add_field(name='Autosave', value=f"{'Enabled' if slime_vars.autosave_status is True else 'Disabled'} ({slime_vars.autosave_interval}min)", inline=False)
        embed.add_field(name='Address', value=f"IP: ||`{backend.get_public_ip()}`||\nURL: ||`{slime_vars.server_url}`|| ({backend.ping_url()})", inline=False)
        embed.add_field(name='Location', value=f"`{slime_vars.server_path}`", inline=False)
        embed.add_field(name='Start Command', value=f"`{slime_vars.server_selected[2]}`", inline=False)  # Shows server name, and small description.
        await ctx.send(embed=embed)

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
            await server_command('save-all')
            await asyncio.sleep(3)
            await server_command('stop')
        else:
            await server_command('say ---WARNING--- Server will halt in 15s!')
            await ctx.send("***Halting Minecraft Server in 15s...***")
            await asyncio.sleep(10)
            await server_command('say ---WARNING--- 5s left!')
            await asyncio.sleep(5)
            await server_command('save-all')
            await asyncio.sleep(3)
            await server_command('stop')

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

        await server_command('say ---WARNING--- Server Rebooting...')
        lprint(ctx, "Restarting Server")
        await ctx.send("***Restarting Minecraft Server...*** :repeat:")
        await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await asyncio.sleep(3)
        await ctx.invoke(self.bot.get_command('serverstart'))

    @commands.command(aliases=['lversion', 'lver', 'lv'])
    async def latestversion(self, ctx):
        """Gets latest Minecraft server version number from official website."""

        response = backend.check_latest_version()
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
        server = backend.get_latest_version()  # Updats server.jar file.
        if server:
            await ctx.send(f"Downloaded latest version: `{server}`\nNext launch may take longer than usual.")
            await asyncio.sleep(3)
        else: await ctx.send("**ERROR:** Updating server failed. Suggest restoring from a backup if updating corrupted any files.")
        lprint(ctx, "Server Updated")

async def setup(bot):
    await bot.add_cog(Basics(bot))
    await bot.add_cog(World(bot))
    await bot.add_cog(Server(bot))
