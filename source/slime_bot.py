import discord, subprocess, random, asyncio, datetime, os, sys, time
from discord.ext import commands, tasks
#from discord_components import DiscordComponents, Button
from discord_components import DiscordComponents, Button, ButtonStyle,  Select, SelectOption, ComponentsBot
from backend_functions import lprint, format_args, server_command, server_status
import backend_functions, slime_vars

__version__ = "5.1P"
__date__ = '2022/01/02'
__author__ = "DT"
__email__ = "dt01@pm.me"
__license__ = "GPL 3"
__status__ = "Development"

# Exits script if no token.
if os.path.isfile(slime_vars.bot_token_file):
    with open(slime_vars.bot_token_file, 'r') as file:
        TOKEN = file.readline()
else:
    print("Missing Token File:", slime_vars.bot_token_file)
    sys.exit()

# Make sure this doesn't conflict with other bots.
bot = ComponentsBot(command_prefix='?', help_command=None)
channel = None

# ========== Extra: Functions, Variables, Templates, etc
teleport_selection = [None, None, None]  # Target, Destination, Target's original location.
player_selection = None
restore_world_selection = restore_server_selection = None
current_components = []

@bot.event
async def on_ready():
    global channel

    await bot.wait_until_ready()

    lprint(f"Bot PRIMED (v{__version__})")

    if slime_vars.channel_id:
        channel = bot.get_channel(slime_vars.channel_id)
        await channel.send('**Bot PRIMED** :white_check_mark:')

        backend_functions.channel_set(channel)  # Needed to set global discord_channel variable.
        await backend_functions.server_status()

        await channel.send(content='Use `?cp` for Control Panel. `?stats` Server Status page. `?help` for all commands.',
                           components=[[Button(label="Start/Stop Servers", emoji='\U0001F3AE', custom_id="games"),
                                        Button(label="Control Panel", emoji='\U0001F39B', custom_id="controlpanel"),
                                        Button(label="Status Page", emoji='\U00002139', custom_id="serverstatus")]])

@bot.event
async def on_button_click(interaction):
    # Need to respond with type=6, or proceeding code will execute twice.
    await interaction.respond(type=6)

    if interaction.custom_id == '_teleport_selected':
        teleport_selection[2] = await backend_functions.get_location(teleport_selection[0])

    # Runs function of same name as button's .custom_id variable. e.g. _teleport_selected()
    ctx = await bot.get_context(interaction.message)
    await ctx.invoke(bot.get_command(str(interaction.custom_id)))

@bot.event
async def on_select_option(interaction):
    global player_selection, restore_world_selection, restore_server_selection

    await interaction.respond(type=6)

    # Updates teleport_selection corresponding value based on which selection box is updated.
    if interaction.custom_id == 'teleport_target': teleport_selection[0] = interaction.values[0]
    if interaction.custom_id == 'teleport_destination': teleport_selection[1] = interaction.values[0]

    # World/server backup panel
    if interaction.custom_id == 'restore_server_selection': restore_server_selection = interaction.values[0]
    if interaction.custom_id == 'restore_world_selection': restore_world_selection = interaction.values[0]

    if interaction.custom_id == 'player_select': player_selection = interaction.values[0]

async def _delete_current_components():
    """Clears out used components so user don't run in to problems and conflicts."""

    global current_components

    for i in current_components:
        try: await i.delete()
        except: pass
    current_components = []

async def get_log_lines(ctx, game_name, lines, file_path, **kwargs):
    """Get Log lines from game server logs."""

    log_mode = True
    if 'filter_mode' in kwargs: log_mode = False

    await ctx.send(f"***Getting {lines} {game_name} Log Lines...*** :tools:")
    log_data = backend_functions.server_log(file_path=file_path, lines=lines, return_reversed=True, log_mode=log_mode, **kwargs)
    for line in log_data.split('\n'):
        if line: await ctx.send(f"`{line}`")
    await ctx.send("-----END-----")
    lprint(ctx, f"Fetched {game_name} Log: {lines}")


# ========== Other Games: Valheim, Project Zomboid
class Other_Games(commands.Cog):
    def __init__(self, bot):
        self.ip_text = f'URL: `{slime_vars.server_url}`\nIP: `{backend_functions.get_public_ip()}` (Use if URL not working)'
        self.valheim_text = f"{self.ip_text}\nPassword: `{slime_vars.valheim_password}`"
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        await ctx.send("""```
?games        - Show start/stop buttons for game.
?info         - Get server address(s) and password(s).

Valheim:
  ?vstart     - Start Valheim Server.
  ?vstop      - Stop server.
  ?vstatus    - Check online status.
  ?vhelp      - Shows instructions for how to join server.
  ?vlog       - Show X log lines. e.g. ?vlog 25.
  ?v/ COMMAND - Send command to vhserver.
    Usage: ?v/ setaccesslevel yeeter admin, ?v/ kickuser yeeter, etc...
        
Project Zomboid:
  ?zstart     - Start Project Zomboid Server.
  ?zstop      - Stop server.
  ?zstatus    - Check online status.
  ?zsave      - Saves game.
  ?zlog       - Show X log lines. e.g. ?zlog 25.
  ?z/ COMMAND - Send command to server.
    
Minecraft:
  ?mstart     - Start Minecraft server. 
  ?mstop      - Stop Minecraft server.
  ?mstatus    - Minecraft server info.
  ?help2      - All Minecraft and slime_bot commands.
```""")
        lprint(ctx, "Show help page.")

    @commands.command(aliases=['address', 'infopage'])
    async def info(self, ctx):
        await ctx.send(f"""
{self.ip_text}
Password for Valheim: `{slime_vars.valheim_password}`
""")
        lprint(ctx, "Show info page.")

    @commands.command(aliases=['vhelp'])
    async def valheimhelp(self, ctx):
        await ctx.invoke(self.bot.get_command("valheimstatus"))
        await ctx.send("Join Server: Start Game > (pick character) Start > Join Game tab > Join IP > enter password if needed.")
        await ctx.send(file=discord.File(rf'{slime_vars.bot_files_path}/valheim_info.png'))

    @commands.command(aliases=['servers', 'game'])
    async def games(self, ctx):
        """Quickly start/stop games."""

        await ctx.send("**Valheim** :axe:", components=[[
            Button(label="Start", custom_id="valheimstart"),
            Button(label="Stop", custom_id="valheimstop"),
            Button(label="Status", custom_id="valheimstatus")
            ]])

        await ctx.send("**Zomboid** :zombie:", components=[[
            Button(label="Start", custom_id="zomboidstart"),
            Button(label="Stop", custom_id="zomboidstop"),
            Button(label="Status", custom_id="zomboidstatus")
            ]])

        await ctx.send("**Minecraft** :pick:", components=[[
            Button(label="Start", custom_id="serverstart"),
            Button(label="Stop", custom_id="serverstop"),
            Button(label="Status", custom_id="serverstatus")
        ]])

    @commands.command(aliases=['v/', 'vcommand'])
    async def valheimcommand(self, ctx, *command):
        """Sends command to vhserver"""

        command = format_args(command)
        backend_functions.valheim_command(command)
        await ctx.send("Sent Command to vhserver")

        lprint(ctx, "Sent Valheim command: " + command)

    @commands.command(aliases=['vstart', 'startvalheim', 'vlaunch'])
    async def valheimstart(self, ctx):
        """Starts Valheim server."""

        vhserver_output = str(subprocess.check_output([f'{slime_vars.valheim_path}/vhserver', 'details']))
        if vhserver_output.find('STARTED') != -1:
            await ctx.send(f"Valheim Server **Online**.\n{self.valheim_text}")
        else:
            await ctx.send("***Launching Valheim Server...*** :rocket:\nPlease wait about 15s before attempting to connect.")
            await ctx.send(f"{self.valheim_text}")
            backend_functions.valheim_command('start')
        lprint(ctx, "Launching Valheim Server")

    @commands.command(aliases=['vstop', 'stopvalheim'])
    async def valheimstop(self, ctx):
        """Stops Valheim server."""

        await ctx.send("**Halted Valheim Server** :stop_sign:")
        backend_functions.valheim_command('stop')
        lprint(ctx, "Halting Valheim Server")

    @commands.command(aliases=['vstatus', 'vinfo', 'vstat'])
    async def valheimstatus(self, ctx):
        """Checks valheim server active status using 'vhserver details' command."""

        await ctx.send("***Checking Valheim Server Status...***")

        vhserver_output = str(subprocess.check_output([f'{slime_vars.valheim_path}/vhserver', 'details']))
        if vhserver_output.find('STARTED') != -1:
            await ctx.send(f"Valheim Server **Online**.\n{self.valheim_text}")
        elif vhserver_output.find('STOPPED') != -1:
            await ctx.send("Valheim Server **Offline**.\nUse `?vstart` to launch server.")
        else: await ctx.send("Unable to check status.")
        lprint(ctx, 'Checked Valheim Status.')

    @commands.command(aliases=['vlog'])
    async def valheimlog(self, ctx, lines=10):
        """Show Valheim log lines."""

        # Skips '(Filename: ./Runtime/Export/Debug/Debug.bindings.h Line: 39)' lines by using the year as filter e.g. '01/10/2022 23:57:51: clone 292'
        await get_log_lines(ctx, 'Valheim', lines, slime_vars.valheim_log_path, match_lines=lines, filter_mode=True, match=str(datetime.datetime.today().year)[-2:])

    # ===== Project Zomboid
    @commands.command(aliases=['zcommand', 'z/'])
    async def zomboidcommand(self, ctx, *command):
        """
        Pass command directly to Project Zomboid server.

        Args:
            *command str: Server command, do not include the slash /.

        Note: Currently no feedback.
        """

        command = format_args(command)
        backend_functions.zomboid_command(f"{command}")
        await asyncio.sleep(1)
        ctx.invoke(self.bot.get_command('zlog'))

        lprint(ctx, "Sent Zomboid command: " + command)

    @commands.command(aliases=['zstart', 'startzomboid'])
    async def zomboidstart(self, ctx):
        """Starts Project Zomboid server."""

        # Checks if server is online first.
        random_number = str(random.random())
        backend_functions.zomboid_command(random_number)
        await asyncio.sleep(1)
        log_data = backend_functions.server_log(random_number, file_path=f'/home/{slime_vars.user}/Zomboid/server-console.txt')
        if log_data:
            await ctx.send(f"Project Zomboid Server **Online**\n{self.ip_text}")
        else:  # Launches if not online already.
            backend_functions.zomboid_command(f'cd /home/{slime_vars.user}/.steam/steam/steamapps/common/Project\ Zomboid\ Dedicated\ Server/')
            backend_functions.zomboid_command(f'./start-server.sh')
            await ctx.send(f"***Launching Project Zomboid Server...*** :rocket:\n{self.ip_text}\nPlease wait about 30s before attempting to connect.")
        lprint(ctx, "Launching Project Zomboid Server")

    @commands.command(aliases=['zstop', 'stopzomboid'])
    async def zomboidstop(self, ctx):
        """Stops Project Zomboid server."""

        backend_functions.zomboid_command('quit')
        await ctx.send("**Halted Project Zomboid Server** :stop_sign:")

        lprint(ctx, "Project Zomboid Stopped")

    @commands.command(aliases=['zstatus', 'statuszomboid', 'zstat'])
    async def zomboidstatus(self, ctx):
        """Checks valheim server active status using 'vhserver details' command."""

        await ctx.send("***Checking Project Zomboid Server Status...***")

        random_number = str(random.random())
        backend_functions.zomboid_command(random_number)
        await asyncio.sleep(1)
        log_data = backend_functions.server_log(random_number, file_path=f'/home/{slime_vars.user}/Zomboid/server-console.txt')
        if log_data:
            await ctx.send(f"Project Zomboid Server **Online**.\n{self.ip_text}")
        else: await ctx.send("Project Zomboid Server **Offline**.\nUse `?zstart` to launch server.")
        lprint(ctx, 'Checked Zomboid Status.')

    @commands.command(aliases=['zlog'])
    async def zomboidlog(self, ctx, lines=10):
        """Show Project Zomboid log lines."""

        await get_log_lines(ctx, 'Zomboid', lines,f'/home/{slime_vars.user}/Zomboid/server-console.txt')

    @commands.command(aliases=['zsave', 'savezomboid'])
    async def zomboidsave(self, ctx):
        """Save Project Zomboid."""

        backend_functions.zomboid_command('save')
        await ctx.send("World Saved")

        lprint(ctx, "Saved Project Zomboid")

# ========== Basics: Say, whisper, online players, server command pass through.
class Basics(commands.Cog):

    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['mcommand', 'm/'])
    async def servercommand(self, ctx, *command):
        """
        Pass command directly to server.

        Args:
            *command str: Server command, do not include the slash /.

        Usage:
            ?command broadcast Hello Everyone!
            ?/ list

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
            *msg str: Message to broadcast.

        Usage:
            ?s Hello World!
        """

        msg = format_args(msg, return_empty_str=True)

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
            player str(''): Player name, casing does not matter.
            *msg str: The message, no need for quotes.

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
    async def chatlog(self, ctx, lines=15):
        """
        Shows chat log. Does not include whispers.

        Args:
            lines int(15): How many log lines to look through. This is not how many chat lines to show.
        """

        await ctx.send(f"***Loading {lines} Chat Log...*** :speech_left:")

        log_data = backend_functions.server_log(']: <', match_lines=lines, filter_mode=True, return_reversed=True)
        try:
            log_data = log_data.strip().split('\n')
        except:
            await ctx.send("**ERROR:** Problem fetching chat logs, there may be nothing to fetch.")
            return False

        for line in log_data:
            try:
                line = line.split(']')
                await ctx.send(f"`{str(line[0][1:] + ':' + line[2][1:])}`")
            except: pass

        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched chat log")

# ========== Player: gamemode, kill, tp, etc
class Player(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['pl', 'playerlist', 'listplayers', 'list'])
    async def players(self, ctx):
        """Show list of online players."""

        player_list = await backend_functions.get_player_list()

        await ctx.send("***Fetching Player List...***")
        if not player_list:
            await ctx.send(f"No players online. ¯\_(ツ)_/¯")
        else:
            new_player_list = []
            for i in player_list[0]:
                new_player_list.append(f'`{i} ({await backend_functions.get_location(i)})`')
            await ctx.send(player_list[1] + '\n' + '\n'.join(new_player_list))
            await ctx.send("-----END-----")

        lprint(ctx, "Fetched player list")

    @commands.command(aliases=['playerkill', 'pk'])
    async def kill(self, ctx, target='', *reason):
        """
        Kill a player.

        Args:
            target str(''): Target player, casing does not matter.
            *reason str: Reason for kill, do not put in quotes.

        Usage:
            ?kill Steve Because he needs to die!
            ?pk Steve
        """

        if not target:
            await ctx.send("Usage: `?kill <player> [reason]`\nExample: `?kill MysticFrogo 5 Because he killed my dog!`")
            return False

        reason = format_args(reason)
        if not await server_command(f"say ---WARNING--- {target} will be EXTERMINATED! : {reason}"): return

        await server_command(f'kill {target}')

        await ctx.send(f"`{target}` :gun: assassinated!")
        lprint(ctx, f"Killed: {target}")

    @commands.command(aliases=['delayedkill', 'delayedplayerkill', 'waitkill', 'dw'])
    async def killwait(self, ctx, target='', delay=5, *reason):
        """
        Kill player after time elapsed.

        Args:
            target str(''): Target player.
            delay int(5): Wait time in seconds.
            *reason str: Reason for kill.

        Usage:
            ?delayedkill Steve 5 Do I need a reason?
            ?pk Steve 15
        """

        reason = format_args(reason)
        if not target:
            await ctx.send("Usage: `?killwait <player> <seconds> [reason]`\nExample: `?killwait MysticFrogo 5 Because he took my diamonds!`")
            return False

        if not await server_command(f"say ---WARNING--- {target} will self-destruct in {delay}s : {reason}"): return

        await ctx.send(f"Killing {target} in {delay}s :bomb:")
        await asyncio.sleep(delay)
        await server_command(f'kill {target}')

        await ctx.send(f"`{target}` soul has been freed.")
        lprint(ctx, f"Delay killed: {target}")

    @commands.command(aliases=['killallplayers', 'kilkillkill'])
    async def _killplayers(self, ctx):
        await ctx.send("All players killed!")
        await backend_functions.server_command('kill @a')
        lprint(ctx, 'Killed: All Players')

    @commands.command(aliases=['killeverything', 'killallentities'])
    async def _killentities(self, ctx):
        await ctx.send("All entities killed!")
        await backend_functions.server_command('kill @e')
        lprint(ctx, 'Killed: All Entities')

    @commands.command(aliases=['killrandom', 'killrandomplayer'])
    async def _killrando(self, ctx):
        await ctx.send("Killed random player! :game_die::knife:")
        await backend_functions.server_command('kill @r')
        lprint(ctx, 'Killed: Random Player')

    @commands.command()
    async def _kill_selected(self, ctx):
        """Kills selected player from player panel."""

        await ctx.invoke(self.bot.get_command('kill'), target=player_selection)

    @commands.command(aliases=['tp'])
    async def teleport(self, ctx, target='', *destination):
        """
        Teleport player to another player.

        Args:
            player str(''): Player to teleport.
            target str(''): Destination, player to teleport to.
            *reason str: Reason for teleport.

        Usage:
            ?teleport Steve Jesse I wanted to see him
            ?tp Jesse Steve
        """

        global teleport_selection
        teleport_selection = [None, None, None]

        # Allows you to teleport to coordinates.
        try: destination = ' '.join(destination)
        except: destination = destination[0]

        # Will not show select components if received usable parameters.
        if not target or not destination:
            await ctx.send("Can use: `?teleport <player> <target_player> [reason]`\nExample: `?teleport R3diculous MysticFrogo I need to see him now!`")

            players = await backend_functions.get_player_list()  # Get list of online players.
            if not players:
                await ctx.send("No players online")
                return

            # Selections updates teleport_selections list, which will be used in _teleport_selected() when button clicked.
            await ctx.send("**Teleport**", components=[
                Select(
                    custom_id="teleport_target",
                    placeholder="Target",
                    options=[SelectOption(label='All Players', value='@a')] +
                            [SelectOption(label='Random Player', value='@r')] +
                            [SelectOption(label=i, value=i) for i in players[0]],
                ),
                Select(custom_id="teleport_destination",
                       placeholder="Destination",
                       options=[SelectOption(label=i, value=i) for i in players[0]] +
                               [SelectOption(label='Random Player', value='@r')],
                       ),
                [Button(label='Teleport', custom_id='_teleport_selected'),
                 Button(label='Return', custom_id='_return_selected')]
            ])

        else:
            if not await server_command(f"say ---INFO--- Teleporting {target} to {destination} in 5s"): return
            await ctx.send(f"***Teleporting in 5s...***")

            # Gets coordinates for target and destination.
            target_info = f'{target} ~ {await backend_functions.get_location(target)}'
            dest_coord = await backend_functions.get_location(destination)
            destination_info = f'{destination}{" ~ " + dest_coord if dest_coord else ""}'

            await asyncio.sleep(5)
            await server_command(f"tp {target} {destination}")

            await ctx.send(f"**Teleported:** `{target_info}` to `{destination_info}` :zap:")
            lprint(ctx, f"Teleported: ({target_info}) to ({destination_info})")

    @commands.command()
    async def _teleport_selected(self, ctx):
        """Teleports selected targets from ?teleport command when use Teleport! button."""

        await ctx.invoke(self.bot.get_command('teleport'), teleport_selection[0], teleport_selection[1])

    @commands.command()
    async def _return_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('teleport'), teleport_selection[0], teleport_selection[2])

    @commands.command(aliases=['playerlocation', 'locateplayer', 'locate', 'location', 'playercoordinates'])
    async def playerlocate(self, ctx, player=''):
        """Gets player's location coordinates."""

        if location := backend_functions.get_location(player):
            await ctx.send(f"Located `{player}`: `{location}`")
            lprint(ctx, f"Located {player}: {location}")
            return location

        await ctx.send(f"**ERROR:** Could not get location.")

    @commands.command()
    async def _locate_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('playerlocate'), player=player_selection)

    @commands.command(aliases=['gm'])
    async def gamemode(self, ctx, player='', mode='', *reason):
        """
        Change player's gamemode.

        Args:
            player str(''): Target player.
            mode str(''): Game mode survival|adventure|creative|spectator.
            *reason str: Optional reason for gamemode change.

        Usage:
            ?gamemode Steve creative In creative for test purposes.
            ?gm Jesse survival
        """

        if not player or mode not in ['survival', 'creative', 'spectator', 'adventure']:
            await ctx.send(f"Usage: `?gamemode <name> <mode> [reason]`\nExample: `?gamemode MysticFrogo creative`, `?gm R3diculous survival Back to being mortal!`")
            return False

        reason = format_args(reason)
        if not await server_command(f"say {player} now in {mode} : {reason}"): return

        await server_command(f"gamemode {mode} {player}")

        await ctx.send(f"`{player}` is now in `{mode.upper()}` indefinitely.")
        lprint(ctx, f"Set {player} to: {mode}")

    @commands.command(aliases=['gamemodetimelimit', 'timedgm', 'gmtimed', 'gmt'])
    async def gamemodetimed(self, ctx, player='', mode='', duration=60, *reason):
        """
        Change player's gamemode for specified amount of seconds, then will change player back to survival.

        Args:
            player str(''): Target player.
            mode str('creative'): Game mode survival/adventure/creative/spectator. Default is creative for 30s.
            duration int(30): Duration in seconds.
            *reason str: Reason for change.

        Usage:
            ?gamemodetimed Steve spectator Steve needs a time out!
            ?tgm Jesse adventure Jesse going on a adventure.
        """

        if not player or mode not in ['survival', 'creative', 'spectator', 'adventure']:
            await ctx.send("Usage: `?gamemodetimed <player> <mode> <seconds> [reason]`\nExample: `?gamemodetimed MysticFrogo spectator 120 Needs a time out`")
            return False

        reason = format_args(reason)
        if not await server_command(f"say ---INFO--- {player.upper()} set to {mode} for {duration}s : {reason}"): return

        await server_command(f"gamemode {mode} {player}")
        await ctx.send(f"`{player}` set to `{mode}` for `{duration}s` :hourglass:")
        lprint(ctx, f"Set gamemode: {player} for {duration}s")

        await asyncio.sleep(duration)
        await server_command(f"say ---INFO--- Times up! {player} is now back to SURVIVAL.")
        await server_command(f"gamemode survival {player}")
        await ctx.send(f"`{player}` is back to survival.")

    @commands.command()
    async def _survival_selected(self, ctx):
        """Changes selected player to survival."""

        await ctx.invoke(self.bot.get_command('gamemode'), player=player_selection, mode='survival')

    @commands.command()
    async def _adventure_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('gamemode'), player=player_selection, mode='adventure')

    @commands.command()
    async def _creative_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('gamemode'), player=player_selection, mode='creative')

    @commands.command()
    async def _spectator_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('gamemode'), player=player_selection, mode='spectator')

    @commands.command(aliases=['clear'])
    async def clearinventory(self, ctx, target):
        """Clears player inventory."""

        if not target:
            await ctx.send("Usage: `?clear <player>")
            return False

        if not await server_command(f"say ---WARNING--- {target} will lose everything!"): return

        await server_command(f'clear {target}')

        await ctx.send(f"`{target}` inventory cleared")
        lprint(ctx, f"Cleared: {target}")

    @commands.command()
    async def _clear_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('clearinventory'), target=player_selection)

# ========== Permissions: Ban, whitelist, Kick, OP.
class Permissions(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def kick(self, ctx, player='', *reason):
        """
        Kick player from server.

        Args:
            player str(''): Player to kick.
            reason str: Optional reason for kick.

        Usage:
            ?kick Steve Because he was trolling
            ?kick Jesse
        """

        if not player:
            await ctx.send("Usage: `?kick <player> [reason]`\nExample: `?kick R3diculous Trolling too much`")
            return False

        reason = format_args(reason)
        if not await server_command(f'say ---WARNING--- {player} will be ejected from server in 5s : {reason}'): return

        await asyncio.sleep(5)
        await server_command(f"kick {player}")

        await ctx.send(f"`{player}` is outta here :wave:")
        lprint(ctx, f"Kicked: {player}")

    @commands.command(aliases=['exile', 'banish'])
    async def ban(self, ctx, player='', *reason):
        """
        Ban player from server.

        Args:
            player str(''): Player to ban.
            reason str: Reason for ban.

        Usage:
            ?ban Steve Player killing
            ?ban Jesse
        """

        if not player:
            await ctx.send("Usage: `?ban <player> [reason]`\nExample: `?ban MysticFrogo Bad troll`")
            return False

        reason = format_args(reason)
        if not await server_command(f"say ---WARNING--- Banishing {player} in 5s : {reason}"):
            return

        await asyncio.sleep(5)

        await server_command(f"ban {player} {reason}")

        await ctx.send(f"Dropkicked and exiled: `{player}` :no_entry_sign:")
        lprint(ctx, f"Banned {player} : {reason}")

    @commands.command()
    async def _kick_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('kick'), player=player_selection)

    @commands.command()
    async def _ban_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('ban'), player=player_selection)

    @commands.command(aliases=['unban'])
    async def pardon(self, ctx, player='', *reason):
        """
        Pardon (unban) player.

        Args:
            player str(''): Player to pardon.
            *reason str: Reason for pardon.

        Usage:
            ?pardon Steve He has turn over a new leaf.
            ?unban Jesse
        """

        if not player:
            await ctx.send("Usage: `?pardon <player> [reason]`\nExample: `?ban R3diculous He has been forgiven`")
            return False

        reason = format_args(reason)
        if not await server_command(f"say ---INFO--- {player} has been vindicated: {reason} :tada:"):return

        await server_command(f"pardon {player}")

        await ctx.send(f"Cleansed `{player}` :flag_white:")
        lprint(ctx, f"Pardoned {player} : {reason}")

    @commands.command(aliases=['bl', 'bans'])
    async def banlist(self, ctx):
        """Show list of current bans."""

        # Gets online players, formats output for Discord depending on using RCON or reading from server log.
        if not await server_status(): return

        banned_players = ''
        response = await server_command("banlist")[0]

        if slime_vars.use_rcon is True:
            if 'There are no bans' in response:
                banned_players = 'No exiles!'
            else:
                data = response.split(':', 1)
                for line in data[1].split('.'):
                    line = backend_functions.remove_ansi(line)
                    line = line.split(':')
                    reason = backend_functions.remove_ansi(line[-1].strip())  # Sometimes you'll get ansi escape chars in your reason.
                    player = line[0].split(' ')[0].strip()
                    banner = line[0].split(' ')[-1].strip()
                    if len(player) < 2:
                        continue
                    banned_players += f"`{player}` banned by `{banner}` : `{reason}`\n"

                banned_players += data[0] + '.'  # Gets line that says 'There are x bans'.

        else:
            if log_data := backend_functions.server_log('banlist'):
                for line in filter(None, log_data.split('\n')):  # Filters out blank lines you sometimes get.
                    if 'There are no bans' in line:
                        banned_players = 'No exiled ones!'
                        break
                    elif 'There are' in line:
                        banned_players += line.split(':')[-2]
                        break

                    # Gets relevant data from current log line, and formats it for Discord output.
                    # Example line: Slime was banned by Server: No reason given
                    # Extracts Player name, who banned the player, and the reason.
                    ban_log_line = line.split(':')[-2:]
                    player = ban_log_line[0].split(' ')[1].strip()
                    banner = ban_log_line[0].split(' ')[-1].strip()
                    reason = ban_log_line[-1].strip()
                    banned_players += f"`{player}` banned by `{banner}` : `{reason}`\n"
            else: banned_players = '**ERROR:** Trouble fetching ban list.'

        await ctx.send(banned_players)
        lprint(ctx, f"Fetched banned list")

    @commands.command(aliases=['wl', 'whitel', 'white', 'wlist'])
    async def whitelist(self, ctx, arg='', arg2=''):
        """
        Whitelist commands. Turn on/off, add/remove, etc.

        Args:
            arg str(''): User passed in arguments for whitelist command, see below for arguments and usage.
            player str(''): Specify player or to specify more options for other arguments, like enforce for example.

        Discord Args:
            list: Show whitelist, same as if no arguments.
            add/add <player>: Player add/remove to whitelist.
            on/off: Whitelist enable/disable
            reload: Reloads from whitelist.json file.
            enforce <status/on/off>: Changes 'enforce-whitelist' in server properties file.
                Kicks players that are not on the whitelist when using ?whitelist reload command.
                Server reboot required for enforce-whitelist to take effect.

        Usage:
            ?whitelist list
            ?whitelist add MysticFrogo
            ?whitelist enforce on
            ?whitelist on
            ?whitelist reload
        """

        # Checks if inputted any arguments.
        if not arg: await ctx.send(f"\nUsage Examples: `?whitelist add MysticFrogo`, `?whitelist on`, `?whitelist enforce on`, use `?help whitelist` or `?help2` for more.")

        # Checks if can send command to server.
        if not await server_status():
            await ctx.send("Server Offline.")
            return
        # Enable/disable whitelisting.
        if arg.lower() in backend_functions.enable_inputs:
            await server_command('whitelist on')
            await ctx.send("**Whitelist ACTIVE** ")
            lprint(ctx, f"Whitelist: Enabled")
        elif arg.lower() in backend_functions.disable_inputs:
            await server_command('whitelist off')
            await ctx.send("**Whitelist INACTIVE**")
            lprint(ctx, f"Whitelist: Disabled")

        # Add/remove user to whitelist (one at a time).
        elif arg == 'add' and arg2:
            await server_command(f"whitelist {arg} {arg2}")
            await ctx.send(f"Added `{arg2}` to whitelist  :page_with_curl::pen_fountain:")
            lprint(ctx, f"Added to whitelist: {arg2}")
        elif arg == 'remove' and arg2:
            await server_command(f"whitelist {arg} {arg2}")
            await ctx.send(f"Removed `{arg2}` from whitelist.")
            lprint(ctx, f"Removed from whitelist: {arg2}")

        # Reload server whitelisting feature.
        elif arg == 'reload':
            await server_command('whitelist reload')
            await ctx.send("***Reloading Whitelist...***\nIf `enforce-whitelist` property is set to `true`, players not on whitelist will be kicked.")

        # Check/enable/disable whitelist enforce feature.
        elif arg == 'enforce' and (not arg2 or 'status' in arg2):  # Shows if passed in ?enforce-whitelist status.
            await ctx.invoke(self.bot.get_command('properties'), 'enforce-whitelist')
            await ctx.send(f"\nUsage Examples: `?whitelist enforce true`, `?whitelist enforce false`.")
            return False
        elif arg == 'enforce' and arg2 in ['true', 'on']:
            await ctx.invoke(self.bot.get_command('properties'), 'enforce-whitelist', 'true')
        elif arg == 'enforce' and arg2 in ['false', 'off']:
            await ctx.invoke(self.bot.get_command('properties'), 'enforce-whitelist', 'false')

        # List whitelisted.
        elif not arg or arg == 'list':
            if slime_vars.use_rcon:
                log_data = await server_command('whitelist list')[1]
                log_data = backend_functions.remove_ansi(log_data).split(':')
            else:
                await server_command('whitelist list')
                # Parses log entry lines, separating 'There are x whitelisted players:' from the list of players.
                log_data = backend_functions.server_log('whitelisted players:')
                if not log_data:
                    await ctx.send('No whitelisted')
                    return
                await asyncio.sleep(1)
                log_data = log_data.split(':')[-2:]

            await ctx.send('**Whitelisted** :page_with_curl:')
            # Then, formats player names in Discord `player` markdown.
            players = [f"`{player.strip()}`" for player in log_data[1].split(', ')]
            await ctx.send(f"{log_data[0].strip()}\n{', '.join(players)}")
            lprint(ctx, f"Showing whitelist: {log_data[1]}")
            await ctx.send("-----END-----")
            return False
        else: await ctx.send("**ERROR:** Something went wrong.")

    @commands.command(aliases=['ol', 'ops', 'listops'])
    async def oplist(self, ctx):
        """Show list of server operators."""

        op_players = [f"`{i['name']}`" for i in backend_functions.read_json('ops.json')]
        if op_players:
            await ctx.send(f"**OP List** :scroll:")
            await ctx.send('\n'.join(op_players))
        else: await ctx.send("No players are OP.")

        lprint(ctx, f"Fetched server operators list")

    @commands.command(aliases=['op', 'addop'])
    async def opadd(self, ctx, player='', *reason):
        """
        Add server operator (OP).

        Args:
            player str(''): Player to make server operator.
            *reason str: Optional reason for new OP status.

        Usage:
            ?opadd Steve Testing purposes
            ?opadd Jesse
        """

        if not player:
            await ctx.send("Usage: `?op <player> [reason]`\nExample: `?op R3diculous Need to be a God!`")
            return False

        if not await server_status(): return

        reason = format_args(reason)

        if slime_vars.use_rcon:
            command_success = await server_command(f"op {player}")[0]
        else:
            # Checks if successful op by looking for certain keywords in log.
            response = await server_command(f"op {player}")
            command_success = backend_functions.server_log(player, stopgap_str=response[1])

        if command_success:
            await server_command(f"say ---INFO--- {player} is now OP : {reason}")
            await ctx.send(f"**New OP Player:** `{player}`")
        else: await ctx.send("**ERROR:** Problem setting OP status.")
        lprint(ctx, f"New server op: {player}")

    @commands.command(aliases=['oprm', 'rmop', 'deop', 'removeop'])
    async def opremove(self, ctx, player='', *reason):
        """
        Remove player OP status (deop).

        Args:
            player str: Target player.
            reason str: Reason for deop.

        Usage:
            ?opremove Steve abusing goodhood.
            ?opremove Jesse
        """

        if not player:
            await ctx.send("Usage: `?deop <player> [reason]`\nExample: `?op MysticFrogo Was abusing God powers!`")
            return False

        if not await server_status(): return

        reason = format_args(reason)
        if slime_vars.use_rcon:
            command_success = await server_command(f"deop {player}")[0]
        else:
            response = await server_command(f"deop {player}")
            command_success = backend_functions.server_log(player, stopgap_str=response[1])

        if command_success:
            await server_command(f"say ---INFO--- {player} no longer OP : {reason}")
            await ctx.send(f"**Player OP Removed:** `{player}`")
        else: await ctx.send("**ERROR:** Problem removing OP status.")
        lprint(ctx, f"Removed server OP: {player}")

    @commands.command(aliases=['optime', 'opt', 'optimedlimit'])
    async def optimed(self, ctx, player='', time_limit=1, *reason):
        """
        Set player as OP for x seconds.

        Args:
            player str(''): Target player.
            time_limit int(1: Time limit in seconds.

        Usage:
            ?optimed Steve 30 Need to check something real quick.
            ?top jesse 60
        """

        if not player:
            await ctx.send("Usage: `?optimed <player> <minutes> [reason]`\nExample: `?optimed R3diculous Testing purposes`")
            return False

        await server_command(f"say ---INFO--- {player} granted OP for {time_limit}m : {reason}")
        await ctx.send(f"***Temporary OP:*** `{player}` for {time_limit}m :hourglass:")
        lprint(f"Temporary OP: {player} for {time_limit}m")
        await ctx.invoke(self.bot.get_command('opadd'), player, *reason)
        await asyncio.sleep(time_limit * 60)
        await ctx.invoke(self.bot.get_command('opremove'), player, *reason)

    @commands.command()
    async def _opadd_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('opadd'), player=player_selection)

    @commands.command()
    async def _opremove_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('opremove'), player=player_selection)

# ========== World: weather, time.
class World(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['weather', 'setweather'])
    async def weatherset(self, ctx, state='', duration=0):
        """
        Set weather.

        Args:
            state str(''): <clear/rain/thunder>: Weather to change to.
            duration int(0): Duration in seconds.

        Usage:
            ?weatherset rain
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

    @commands.command(aliases=['time', 'settime'])
    async def timeset(self, ctx, set_time=''):
        """
        Set time.

        Args:
            set_time int(''): Set time either using day|night|noon|midnight or numerically.

        Usage:
            ?timeset day
            ?time 12
        """

        if not await server_status(): return

        if set_time:
            await server_command(f"time set {set_time}")
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
        await ctx.send("Daylight cycle ENABLED")
        lprint(ctx, 'Daylight Cycle: Enabled')

    @commands.command(aliases=['diabletime', 'timecycleoff'])
    async def timeoff(self, ctx):
        """Disable day light cycle."""

        await server_command(f'gamerule doDaylghtCycle false')
        await ctx.send("Daylight cycle DISABLED")
        lprint(ctx, 'Daylight Cycle: Disabled')

# ========== Server: autosave, Start/stop, Status, edit property, backup/restore.
class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if slime_vars.autosave_status is True:
            self.autosave_loop.start()
            lprint(f"Autosave task started (interval: {slime_vars.autosave_interval}m)")

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
            arg int(''): turn on/off autosave, or set interval in minutes.

        Usage:
            ?autosave
            ?autosave on
            ?autosave 60
        """

        if not arg: await ctx.send(f"Usage Examples: Update interval (minutes) `?autosave 60`, turn on `?autosave on`.")

        # Parses user input and sets invertal for autosave.
        try: arg = int(arg)
        except: pass
        else:
            slime_vars.autosave_interval = arg
            backend_functions.edit_file('autosave_interval', f" {arg}", slime_vars.slime_vars_file)

        # Enables/disables autosave tasks.loop(). Also edits slime_vars.py file, so autosave state can be saved on bot restarts.
        arg = str(arg)
        if arg.lower() in backend_functions.enable_inputs:
            slime_vars.autosave_status = True
            self.autosave_loop.start()
            backend_functions.edit_file('autosave_status', ' True', slime_vars.slime_vars_file)
            lprint(ctx, f'Autosave: Enabled (interval: {slime_vars.autosave_interval}m)')
        elif arg.lower() in backend_functions.disable_inputs:
            slime_vars.autosave_status = False
            self.autosave_loop.cancel()
            backend_functions.edit_file('autosave_status', ' False', slime_vars.slime_vars_file)
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
            lprint(f"Autosaved (interval: {slime_vars.autosave_interval}m)")

        backend_functions.zomboid_command('save')

    @autosave_loop.before_loop
    async def before_autosaveall_loop(self):
        """Makes sure bot is ready before autosave_loop can be used."""

        await self.bot.wait_until_ready()

    @commands.command(aliases=['check', 'checkstatus', 'statuscheck', 'active'])
    async def servercheck(self, ctx, show_msg=True):
        """Checks if server is online."""

        await server_status(discord_msg=show_msg)
        await ctx.invoke(self.bot.get_command('_control_panel_msg'))

    @commands.command(aliases=['mstatus'])
    async def serverstatus(self, ctx):
        """Shows server active status, version, motd, and online players"""

        embed = discord.Embed(title='Server Status')
        embed.add_field(name='Current Server', value=f"Status: {'**ACTIVE** :green_circle:' if await server_status() is True else '**INACTIVE** :red_circle:'}\nServer: {slime_vars.server_selected[0]}\nDescription: {slime_vars.server_selected[1]}\n", inline=False)
        embed.add_field(name='MOTD', value=f"{backend_functions.server_motd()}", inline=False)
        embed.add_field(name='Version', value=f"{backend_functions.server_version()}", inline=False)
        embed.add_field(name='Address', value=f"IP: ||`{backend_functions.get_public_ip()}`||\nURL: ||`{slime_vars.server_url}`|| ({backend_functions.ping_url()})", inline=False)
        embed.add_field(name='Autosave', value=f"Status: {'**ENABLED**' if slime_vars.autosave_status is True else '**DISABLED**'}\nInterval: **{slime_vars.autosave_interval}** minutes", inline=False)
        embed.add_field(name='Location', value=f"`{slime_vars.server_path}`", inline=False)
        embed.add_field(name='Start Command', value=f"`{slime_vars.server_selected[2]}`", inline=False)  # Shows server name, and small description.
        await ctx.send(embed=embed)

        await ctx.invoke(self.bot.get_command('players'))
        await ctx.invoke(self.bot.get_command('_control_panel_msg'))
        lprint(ctx, "Fetched server status")

    @commands.command(aliases=['log', 'mlog'])
    async def serverlog(self, ctx, lines=10):
        """
        Show server log.

        Args:
            lines int(5): How many most recent lines to show. Max of 20 lines!

        Usage:
            ?serverlog
            ?log 10
        """

        file_path = f"{slime_vars.server_path}/logs/latest.log"
        await ctx.send(f"***Getting {lines} Minecraft Log Lines...*** :tools:")
        log_data = backend_functions.server_log(file_path=file_path, lines=lines, log_mode=True, return_reversed=True)
        for line in log_data.split('\n'):
            await ctx.send(f"`{line}`")
        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched Minecraft Log: {lines}")

    @commands.command(aliases=['startminecraft', 'mstart'])
    async def serverstart(self, ctx):
        """
        Start Minecraft server.

        Note: Depending on your system, server may take 15 to 40+ seconds to fully boot.
        """

        if await server_status() is True:
            await ctx.send("**Server ACTIVE** :green_circle:")
            return False

        await ctx.send(f"***Launching Minecraft Server...*** :rocket:\nAddress: `{slime_vars.server_url}`\nPlease wait about 15s before attempting to connect.")
        backend_functions.server_start()
        await ctx.send("***Fetching Status in 20s...***")
        await asyncio.sleep(20)

        await ctx.invoke(self.bot.get_command('serverstatus'))
        lprint(ctx, "Starting Minecraft Server")

    @commands.command(aliases=['minecraftstop', 'stopminecraft', 'mstop'])
    async def serverstop(self, ctx, now=''):
        """
        Stop Minecraft server, gives players 15s warning.

        Args:
            now str(''): Stops server immediately without giving online players 15s warning.

        Usage:
            ?stop
            ?stop now
        """

        if not await server_status(): return

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
        backend_functions.mc_subprocess = None
        lprint(ctx, "Stopping Server")

    @commands.command(aliases=['rebootserver', 'restartserver', 'serverreboot', 'mrestart'])
    async def serverrestart(self, ctx, now=''):
        """
        Restarts server with 15s warning to players.

        Args:
            now str: Restarts server immediately without giving online players 15s warning.

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

    @commands.command(aliases=['version', 'v', 'serverv'])
    async def serverversion(self, ctx):
        """Gets Minecraft server version."""

        response = backend_functions.server_version()
        await ctx.send(f"Current version: `{response}`")
        lprint("Fetched Minecraft server version: " + response)

    @commands.command(aliases=['lversion', 'lver', 'lv'])
    async def latestversion(self, ctx):
        """Gets latest Minecraft server version number from official website."""

        response = backend_functions.check_latest_version()
        await ctx.send(f"Latest version: `{response}`")
        lprint("Fetched latest Minecraft server version: " + response)

    @commands.command()
    async def propertiesall(self, ctx):
        """Shows full server properties file."""

        await ctx.invoke(self.bot.get_command('properties'), target_property='all')

    @commands.command(aliases=['property', 'p'])
    async def properties(self, ctx, target_property='', *value):
        """
        Check or change a server.properties property. May require restart.

        Note: Passing in 'all' for target property argument (with nothing for value argument) will show all the properties.

        Args:
            target_property str(''): Target property to change, must be exact in casing and spelling and some may include a dash -.
            *value str: New value. For some properties you will need to input a lowercase true or false, and for others you may input a string (quotes not needed).

        Usage:
            ?property motd
            ?property spawn-protection 2
            ?property all
        """

        if not target_property:
            await ctx.send("Usage: `?property <property_name> [new_value]`\nExample: `?property motd`, `?p motd Hello World!`")
            return False

        if value:
            await ctx.send("Property Updated  :memo:")
            value = ' '.join(value)
        else: value = ''

        backend_functions.edit_file(target_property, value)
        fetched_property = backend_functions.edit_file(target_property)
        await asyncio.sleep(2)

        if fetched_property:
            await ctx.send(f"`{fetched_property[0].strip()}`")
            lprint(ctx, f"Server property: {fetched_property[0].strip()}")
        else:
            await ctx.send(f"**ERROR:** 404 Property not found.")
            lprint(f"Server property not found: {target_property}")

    @commands.command(aliases=['serveronlinemode', 'omode', 'om'])
    async def onlinemode(self, ctx, mode=''):
        """
        Check or enable/disable onlinemode property. Restart required.

        Args:
            mode str(''): Update onlinemode property in server.properties file. Must be in lowercase.

        Usage:
            ?onlinemode true
            ?omode false
        """

        if not mode:
            online_mode = backend_functions.edit_file('online-mode')[1]
            await ctx.send(f"online mode: `{online_mode}`")
            lprint(ctx, f"Fetched online-mode state: {online_mode}")
        elif mode in ['true', 'false']:
            backend_functions.edit_file('online-mode', mode)[0]
            server_property = backend_functions.edit_file('online-mode')
            await ctx.send(f"Updated online mode: `{server_property[1]}`")
            await ctx.send("**Note:** Server restart required for change to take effect.")
            lprint(ctx, f"Updated online-mode: {server_property[1].strip()}")
        else: await ctx.send("Need a true or false argument (in lowercase).")

    @commands.command(aliases=['updatemotd', 'servermotd'])
    async def motd(self, ctx, *message):
        """
        Check or Update motd property. Restart required.

        Args:
            *message str: New message for message of the day for server. No quotes needed.

        Usage:
            ?motd
            ?motd YAGA YEWY!
        """

        message = format_args(message, return_empty_str=True)

        if slime_vars.use_rcon:
            motd_property = backend_functions.server_motd()
        elif slime_vars.server_files_access:
            backend_functions.edit_file('motd', message)
            motd_property = backend_functions.edit_file('motd')
        else: motd_property = '**ERROR:** Fetching server motd failed.'

        if message:
            await ctx.send(f"Updated MOTD: `{motd_property[0].strip()}`")
            lprint("Updated MOTD: " + motd_property[1].strip())
        else:
            await ctx.send(f"Current MOTD: `{motd_property[1]}`")
            lprint("Fetched MOTD: " + motd_property[1].strip())

    @commands.command(aliases=['serverrcon'])
    async def rcon(self, ctx, state=''):
        """
        Check RCON status, enable/disable enable-rcon property. Restart required.

        Args:
            state str(''): Set enable-rcon property in server.properties file, true or false must be in lowercase.

        Usage:
            ?rcon
            ?rcon true
            ?rcon false

        """

        if state in ['true', 'false', '']:
            response = backend_functions.edit_file('enable-rcon', state)
            await ctx.send(f"`{response[0]}`")
        else: await ctx.send("Need a true or false argument (in lowercase).")

    @commands.command(aliases=['updateserver', 'su'])
    async def serverupdate(self, ctx, now=''):
        """
        Updates server.jar file by downloading latest from official Minecraft website.

        Note: This will not make a backup beforehand, suggest doing so with ?serverbackup command.

        Args:
            now str(''): Stops server immediately without giving online players 15s warning.
        """

        if 'vanilla' not in slime_vars.server_selected:
            await ctx.send(f"**ERROR:** This command only works with vanilla servers. You have `{slime_vars.server_selected[0]}` selected.")
            return False

        lprint(ctx, "Updating server.jar...")
        await ctx.send("***Updating...*** :arrows_counterclockwise:")

        if await server_status() is True:
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)
        await asyncio.sleep(5)

        await ctx.send("***Downloading latest server.jar***")
        server = backend_functions.get_latest_version()

        if server is True:
            await ctx.send(f"Downloaded latest version: `{server}`")
            await asyncio.sleep(3)
            await ctx.invoke(self.bot.get_command('serverstart'))
        else: await ctx.send("**ERROR:** Updating server failed. Suggest restoring from a backup if updating corrupted any files.")

        lprint(ctx, "Server Updated")

class World_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['worldbackupslist', 'backuplist' 'backupslist', 'wbl'])
    async def worldbackups(self, ctx, amount=10):
        """
        Show world backups.

        Args:
            amount int(10): Number of most recent backups to show.

        Usage:
            ?saves
            ?saves 15
        """

        embed = discord.Embed(title='World Backups :floppy_disk:')
        worlds = backend_functions.fetch_worlds()
        if worlds is False:
            await ctx.send("No world backups found.")
            return False

        for backup in worlds[-amount:]:
            embed.add_field(name=backup[0], value=f"`{backup[1]}`", inline=False)
        await ctx.send(embed=embed)
        await ctx.send("Use `?worldrestore <index>` to restore world save.")

        await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
        lprint(ctx, f"Fetched {amount} world saves")

    @commands.command(aliases=['backupworld', 'newworldbackup', 'worldbackupnew', 'wbn'])
    async def worldbackup(self, ctx, *name):
        """
        new backup of current world.

        Args:
            *name str: Keywords or codename for new save. No quotes needed.

        Usage:
            ?backup everything not on fire
            ?backup Jan checkpoint
        """

        if not name:
            await ctx.send("Usage: `?worldbackup <name>`\nExample: `?worldbackup Before the reckoning`")
            return False
        name = format_args(name)

        if await server_command(f"say ---INFO--- Standby, world is currently being archived. Codename: {name}"):
            await server_command(f"save-all")
            await asyncio.sleep(3)

        await ctx.send("***Creating World Backup...*** :new::floppy_disk:")
        new_backup = backend_functions.backup_world(name)
        if new_backup:
            await ctx.send(f"**New World Backup:** `{new_backup}`")
        else: await ctx.send("**ERROR:** Problem saving the world! || it's doomed!||")

        await ctx.invoke(self.bot.get_command('worldbackupslist'))
        lprint(ctx, "New world backup: " + new_backup)

    @commands.command(aliases=['deleteworldbackup'])
    async def worldbackupdate(self, ctx):
        """Creates world backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('worldbackup'), '')

    @commands.command(aliases=['restoreworld', 'worldbackuprestore', 'wbr'])
    async def worldrestore(self, ctx, index='', now=''):
        """
        Restore a world backup.

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.

        Args:
            index int(''): Get index with ?saves command.
            now str='': Skip 15s wait to stop server. E.g. ?restore 0 now

        Usage:
            ?restore 3
        """

        try: index = int(index)
        except:
            await ctx.send("Usage: `?worldrestore <index> [now]`\nExample: `?worldrestore 0 now`")
            return False

        fetched_restore = backend_functions.get_world_from_index(index)
        lprint(ctx, "World restoring to: " + fetched_restore)
        await ctx.send("***Restoring World...*** :floppy_disk::leftwards_arrow_with_hook:")
        if await server_status():
            await server_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}")
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await ctx.send(f"**Restored World:** `{fetched_restore}`")
        backend_functions.restore_world(fetched_restore)  # Gives computer time to move around world files.
        await asyncio.sleep(5)

        await ctx.send("Start server with `?start` or click button", components=[
            Button(label="Start Server", emoji='\U0001F680', custom_id="serverstart")])

    @commands.command()
    async def _restore_world_selected(self, ctx):
        await _delete_current_components()
        await ctx.invoke(self.bot.get_command('worldrestore'), index=restore_world_selection)

    @commands.command(aliases=['deleteworld', 'wbd'])
    async def worlddelete(self, ctx, index=''):
        """
        Delete a world backup.

        Args:
            index int(''): Get index with ?saves command.

        Usage:
            ?delete 0
        """

        try: index = int(index)
        except:
            await ctx.send("Usage: `?worlddelete <index>`\nExample: `?worlddelete 1`")
            return False

        to_delete = backend_functions.get_world_from_index(index)
        await ctx.send("***Deleting World Backup...*** :floppy_disk::wastebasket:")
        backend_functions.delete_world(to_delete)

        await ctx.send(f"**World Backup Deleted:** `{to_delete}`")
        lprint(ctx, "Deleted world backup: " + to_delete)

    @commands.command()
    async def _delete_world_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('worlddelete'), index=restore_world_selection)
        await ctx.invoke(self.bot.get_command('worldrestorepanel'))

    @commands.command(aliases=['rebirth', 'hades', 'resetworld'])
    async def worldreset(self, ctx, now=''):
        """
        Deletes world save (does not touch other server files).

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        await server_command("say ---WARNING--- Project Rebirth will commence in T-5s!")
        await ctx.send(":fire: **Project Rebirth Commencing** :fire:")
        await ctx.send("**NOTE:** Next launch may take longer.")

        if await server_status() is True:
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await ctx.send("**Finished.**")
        await ctx.send("You can now start the server with `?start`.")

        backend_functions.restore_world(reset=True)
        await asyncio.sleep(3)

        lprint(ctx, "World Reset")

class Server_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['sselect', 'serversselect', 'serverslist', 'ss'])
    async def serverlist(self, ctx, name=''):
        """
        Select server to use all other commands on. Each server has their own world_backups and server_restore folders.

        Args:
            name str(''): name of server to select, use ?selectserver list or without arguments to show list.

        Usage:
            ?selectserver list
            ?selectserver papermc
        """

        if not name or 'list' in name:
            embed = discord.Embed(title='Server List :desktop:')
            for server in slime_vars.server_list.values():
                # Shows server name, description, location, and start command.
                embed.add_field(name=server[0], value=f"Description: {server[1]}\nLocation: `{slime_vars.mc_path}/{slime_vars.server_selected[0]}`\nStart Command: `{server[2]}`", inline=False)
            await ctx.send(embed=embed)
            await ctx.send(f"**Current Server:** `{slime_vars.server_selected[0]}`")
        elif name in slime_vars.server_list.keys():
            backend_functions.server_selected = slime_vars.server_list[name]
            backend_functions.server_path = f"{slime_vars.mc_path}/{slime_vars.server_selected[0]}"
            backend_functions.edit_file('server_selected', f" server_list['{name}']", slime_vars.slime_vars_file)
            await ctx.invoke(self.bot.get_command('restartbot'))
        else: await ctx.send("**ERROR:** Server not found.\nUse `?serverselect` or `?ss` to show list of available servers.")

    @commands.command(aliases=['serverbackupslist', 'sbl'])
    async def serverbackups(self, ctx, amount=10):
        """
        List server backups.

        Args:
            amount int(5): How many most recent backups to show.

        Usage:
            ?serversaves
            ?serversaves 10
        """

        embed = discord.Embed(title='Server Backups :floppy_disk:')
        servers = backend_functions.fetch_servers()

        if servers is False:
            await ctx.send("No server backups found.")
            return False

        for save in servers[-amount:]:
            embed.add_field(name=save[0], value=f"`{save[1]}`", inline=False)
        await ctx.send(embed=embed)

        await ctx.send("Use `?serverrestore <index>` to restore server.")
        await ctx.send("**WARNING:** Restore will overwrite current server. Create backup using `?serverbackup <codename>`.")
        lprint(ctx, f"Fetched {amount} world backups")

    @commands.command(aliases=['deleteserverbackup'])
    async def serverbackupdate(self, ctx):
        """Creates server backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('serverbackup'), '')

    @commands.command(aliases=['backupserver', 'newserverbackup', 'serverbackupnew', 'sbn'])
    async def serverbackup(self, ctx, *name):
        """
        New backup of server files (not just world save).

        Args:
            name str: Keyword or codename for save.

        Usage:
            ?serverbackup Dec checkpoint
        """

        if not name:
            await ctx.send("Usage: `?serverbackup <name>`\nExample: `?serverbackup Everything just dandy`")
            return False

        name = format_args(name)
        await ctx.send(f"***Creating Server Backup...*** :new::floppy_disk:")
        if not await server_command(f"save-all"): return

        await asyncio.sleep(5)
        new_backup = backend_functions.backup_server(name)
        if new_backup:
            await ctx.send(f"**New Server Backup:** `{new_backup}`")
        else: await ctx.send("**ERROR:** Server backup failed! :interrobang:")

        await ctx.invoke(self.bot.get_command('serverbackupslist'))
        lprint(ctx, "New server backup: " + new_backup)

    @commands.command(aliases=['restoreserver', 'serverbackuprestore', 'restoreserverbackup', 'sbr'])
    async def serverrestore(self, ctx, index='', now=''):
        """
        Restore server backup.

        Args:
            index int(''): Get index number from ?serversaves command.
            now str(''): Stop server without 15s wait.

        Usage:
            ?serverrestore 0
        """

        try: index = int(index)
        except:
            await ctx.send("Usage: `?serverrestore <index> [now]`\nExample: `?serverrestore 2 now`")
            return False

        fetched_restore = backend_functions.get_server_from_index(index)
        lprint(ctx, "Server restoring to: " + fetched_restore)
        await ctx.send(f"***Restoring Server...*** :floppy_disk::leftwards_arrow_with_hook:")

        if await server_status() is True:
            await server_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}")
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        if backend_functions.restore_server(fetched_restore):
            await ctx.send(f"**Server Restored:** `{fetched_restore}`")
        else: await ctx.send("**ERROR:** Could not restore server!")

        await ctx.send("Start server with `?start` or click button", components=[
            Button(label="Start Server", emoji='\U0001F680', custom_id="serverstart")])

    @commands.command()
    async def _restore_server_selected(self, ctx):
        await _delete_current_components()
        await ctx.invoke(self.bot.get_command('serverrestore'), index=restore_server_selection)

    @commands.command(aliases=['deleteserver', 'deleteserverrestore', 'serverrestoredelete', 'sbd'])
    async def serverdelete(self, ctx, index=''):
        """
        Delete a server backup.

        Args:
            index int: Index of server save, get with ?serversaves command.

        Usage:
            ?serverdelete 0
            ?serverrm 5
        """

        try: index = int(index)
        except:
            await ctx.send("Usage: `?serverdelete <index>`\nExample: `?serverdelete 3`")
            return False

        to_delete = backend_functions.get_server_from_index(index)
        await ctx.send("***Deleting Server Backup...*** :floppy_disk::wastebasket:")
        backend_functions.delete_server(to_delete)

        await ctx.send(f"**Server Backup Deleted:** `{to_delete}`")
        lprint(ctx, "Deleted server backup: " + to_delete)

    @commands.command()
    async def _delete_server_selected(self, ctx):
        await ctx.invoke(self.bot.get_command('serverdelete'), index=restore_server_selection)
        await ctx.invoke(self.bot.get_command('serverrestorepanel'))

# ========== Extra: restart bot, botlog, get ip, help2.
class Bot_Functions(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def botinfo(self, ctx):
        pass

    @commands.command()
    async def _control_panel_msg(self, ctx):
        """Shows message and button to open the control panel."""

        await ctx.send(content='Use `?cp` for Control Panel. `?stats` Server Status page. `?help` for all commands.',
                       components=[[Button(label="Control Panel", emoji='\U0001F39B', custom_id="controlpanel"),
                                    Button(label="Status Page", emoji='\U00002139', custom_id="serverstatus")]])

    @commands.command(aliases=['buttons', 'dashboard', 'controls', 'panel', 'cp'])
    async def controlpanel(self, ctx):
        """Quick action buttons."""

        await ctx.send("**Control Panel**\nServer:", components=[[
            Button(label="Status Page", emoji='\U00002139', custom_id="serverstatus"),
            Button(label="Stop Server", emoji='\U0001F6D1', custom_id="serverstop")
            if await server_status() else
            Button(label="Start Server", emoji='\U0001F680', custom_id="serverstart"),
            Button(label="Reboot Server", emoji='\U0001F501', custom_id="serverrestart"),
        ], [
            Button(label="Server Version", emoji='\U00002139', custom_id="serverversion"),
            Button(label="Show MotD", emoji='\U0001F4E2', custom_id="motd"),
            Button(label="Show Properties File", emoji='\U0001F527', custom_id="propertiesall"),
            Button(label="Server Logs", emoji='\U0001F4C3', custom_id="serverlog"),
        ]])

        await ctx.send("Saving & Backups:", components=[[
            Button(label="Backup World", emoji='\U0001F195', custom_id="worldbackupdate"),
            Button(label="Backup Server", emoji='\U0001F195', custom_id="serverbackupdate"),
            Button(label='Show World Backups', emoji='\U0001F4BE', custom_id="restoreworldpanel"),
            Button(label="Show Server Backups", emoji='\U0001F4BE', custom_id="restoreserverpanel"),
        ], [
            Button(label="Disable Autosave", emoji='\U0001F504', custom_id="autosaveoff") \
            if slime_vars.autosave_status else
            Button(label="Enable Autosave", emoji='\U0001F504', custom_id="autosaveon"),
            Button(label="Save World", emoji='\U0001F30E', custom_id="saveall"),
        ]])

        await ctx.send("Players:", components=[[
            Button(label="Player List", emoji='\U0001F5B1', custom_id="playerlist"),
            Button(label="Chat Log", emoji='\U0001F5E8', custom_id="chatlog"),
            Button(label="Show Banned", emoji='\U0001F6AB', custom_id="banlist"),
            Button(label="Show Whitelist", emoji='\U0001F4C3', custom_id="whitelist"),
            Button(label="Show OP List", emoji='\U0001F4DC', custom_id="oplist"),
        ], [
            Button(label='Player Panel', emoji='\U0001F39B', custom_id='playerpanel'),
            Button(label='Teleport', emoji='\U000026A1', custom_id='teleport')
        ]])

        await ctx.send("Time & Weather:", components=[[
            Button(label='Day', emoji='\U00002600', custom_id="timeday"),
            Button(label="Night", emoji='\U0001F319', custom_id="timenight"),
            Button(label='Enable Time', emoji='\U0001F7E2', custom_id="timeon"),
            Button(label='Disable Time', emoji='\U0001F534', custom_id="timeoff"),
        ], [
            Button(label='Clear', emoji='\U00002600', custom_id="weatherclear"),
            Button(label="Rain", emoji='\U0001F327', custom_id="weatherrain"),
            Button(label='Thunder', emoji='\U000026C8', custom_id="weatherthunder"),
            Button(label='Enable Weather', emoji='\U0001F7E2', custom_id="weatheron"),
            Button(label='Disable Weather', emoji='\U0001F534', custom_id="weatheroff"),
        ]])

        await ctx.send("Bot:", components=[[
            Button(label='Restart Bot', emoji='\U0001F501', custom_id="restartbot"),
            Button(label='Set Channel ID', emoji='\U0001FA9B', custom_id="setchannelid"),
            Button(label="Bot Logs", emoji='\U0001F4C3', custom_id="botlog"),
        ]])

        await ctx.send("Extra:", components=[[
            Button(label='Refresh Control Panel', emoji='\U0001F504', custom_id="controlpanel"),
            Button(label="Get Address", emoji='\U0001F310', custom_id="ip"),
            Button(label='Website Links', emoji='\U0001F517', custom_id="links"),
        ]])

        lprint(ctx, 'Opened control panel')

    @commands.command(aliases=['sp', 'hiddenpanel'])
    async def secretpanel(self, ctx):
        await ctx.send("**Secret Panel**", components=[[
            Button(label='Kill Players', emoji='\U0001F4A3', custom_id="_killplayers"),
            Button(label="Kill Entities", emoji='\U0001F4A5', custom_id="_killentities"),
            Button(label='Kill Rando', emoji='\U00002753', custom_id="_killrando"),
        ], [
            Button(label='HADES Protocol', emoji='\U0001F480', custom_id="hades"),
        ]])

        lprint(ctx, 'Opened secret panel')

    @commands.command(aliases=['player', 'ppanel'])
    async def playerpanel(self, ctx, player=''):
        """Select player from list (or all, random) and use quick action buttons."""

        global player_selection
        player_selection = None

        players = await backend_functions.get_player_list()  # Gets list of online players
        if not players: players = [[], ["No Players Online"]]  # Lets user know there are no online players
        # Sets selection to player parameter if received one.
        select_playeropt = []
        if player: select_playeropt = [SelectOption(label=player, value=player, default=True)]

        await ctx.send("**Player Panel**", components=[
            Select(custom_id='player_select',
                   placeholder="Select Player",
                   options=select_playeropt +
                           [SelectOption(label='All Players', value='@a')] +
                           [SelectOption(label='Random Player', value='@r')] +
                           [SelectOption(label=i, value=i) for i in players[0]],
                   )])

        await ctx.send('Actions:', components=[[
            Button(label='Kill', emoji='\U0001F52A', custom_id="_kill_selected"),
            Button(label="Clear Inventory", emoji='\U0001F4A5', custom_id="_clear_selected"),
            Button(label='Location', emoji='\U0001F4CD', custom_id="_locate_selected"),
        ], [
            Button(label='Survival', emoji='\U0001F5E1', custom_id="_survival_selected"),
            Button(label='Adventure', emoji='\U0001F5FA', custom_id="_adventure_selected"),
            Button(label='Creative', emoji='\U0001F528', custom_id="_creative_selected"),
            Button(label='Spectator', emoji='\U0001F441', custom_id="_spectator_selected"),
        ], [
            Button(label='OP', emoji='\U000023EB', custom_id="_opadd_selected"),
            Button(label='DEOP', emoji='\U000023EC', custom_id="_opremove_selected"),
            Button(label='Kick', emoji='\U0000274C', custom_id="_kick_selected"),
            Button(label='Ban', emoji='\U0001F6AB', custom_id="_ban_selected"),
        ]])

        lprint(ctx, 'Opened player panel')

    @commands.command(aliases=['restoreworldpanel', 'wrpanel', 'wrp'])
    async def worldrestorepanel(self, ctx):
        """Restore/delete selected world backup."""

        global restore_world_selection, current_components
        restore_world_selection = None  # Resets selection to avoid conflicts.
        await _delete_current_components()  # Clear out used components so you don't run into conflicts and issues.

        backups = backend_functions.fetch_worlds()
        if not backups: await ctx.send("No world backups")

        selection_msg = await ctx.send("**Restore World Panel**", components=[
            Select(custom_id='restore_world_selection',
                   placeholder="Select World Backup",
                   options=[SelectOption(label=i[1], value=i[0], description=i[0]) for i in backups]
                   )])

        button_msg = await ctx.send("Actions:", components=[[
            Button(label='Restore', emoji='\U000021A9', custom_id="_restore_world_selected"),
            Button(label="Delete", emoji='\U0001F5D1', custom_id="_delete_world_selected"),
        ]])

        current_components += selection_msg, button_msg
        lprint(ctx, 'Opened restore world panel')

    @commands.command(aliases=['restoreserverpanel', 'srpanel', 'srp'])
    async def serverrestorepanel(self, ctx):
        """Restore/delete selected server backup."""

        global restore_server_selection, current_components
        restore_server_selection = None
        await _delete_current_components()

        backups = backend_functions.fetch_servers()
        if not backups: await ctx.send("No server backups")

        selection_msg = await ctx.send("**Restore Server Panel**", components=[
            Select(custom_id='restore_server_selection',
                   placeholder="Select Server Backup",
                   options=[SelectOption(label=i[1], value=i[0], description=i[0]) for i in backups]
                   )])

        button_msg = await ctx.send("Actions:", components=[[
            Button(label='Restore', emoji='\U000021A9', custom_id="_restore_server_selected"),
            Button(label="Delete", emoji='\U0001F5D1', custom_id="_delete_server_selected"),
        ]])

        current_components += selection_msg, button_msg
        lprint(ctx, 'Opened restore server panel')

    @commands.command(aliases=['rbot', 'rebootbot', 'botrestart', 'botreboot'])
    async def restartbot(self, ctx, now=''):
        """Restart this bot."""

        await ctx.send("***Rebooting Bot...*** :arrows_counterclockwise: ")
        lprint(ctx, "Restarting bot...")

        if slime_vars.use_subprocess is True:
            await ctx.invoke(self.bot.get_command("serverstop"), now=now)

        os.chdir(slime_vars.bot_files_path)
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['blog'])
    async def botlog(self, ctx, lines=10):
        """
        Show bot log.

        Args:
            lines int(5): Number of most recent lines to show.

        Usage:
            ?botlog
            ?blog 15
        """

        log_data = backend_functions.server_log(file_path=slime_vars.bot_log_file, lines=lines, log_mode=True, return_reversed=True)

        await ctx.send(f"***Getting {lines} Bot Log Lines...*** :tools:")
        # Shows server log line by line.
        for line in log_data.split('\n'):
            await ctx.send(f"`{line}`")

        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched Bot Log: {lines}")

    @commands.command(aliases=['updatebot', 'botupdate'])
    async def gitupdate(self, ctx):
        """Gets update from GitHub."""

        os.chdir(slime_vars.bot_files_path)
        os.system('git pull')

        await ctx.invoke(self.bot.get_command("restartbot"))

    @commands.command()
    async def help2(self, ctx):
        """Shows help page with embed format, using reactions to navigate pages."""

        lprint(ctx, "Fetched help page")
        current_command, embed_page, contents = 0, 1, []
        pages, current_page, page_limit = 3, 1, 15

        def new_embed(page):
            return discord.Embed(title=f'Help Page {page}/{pages} :question:')

        embed = new_embed(embed_page)
        for command in backend_functions.read_csv('command_info.csv'):
            if not command: continue

            embed.add_field(name=command[0], value=f"{command[1]}\n{', '.join(command[2:])}", inline=False)
            current_command += 1
            if not current_command % page_limit:
                embed_page += 1
                contents.append(embed)
                embed = new_embed(embed_page)
        contents.append(embed)

        # getting the message object for editing and reacting
        message = await ctx.send(embed=contents[0])
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        # This makes sure nobody except the command sender can interact with the "menu"
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
                if str(reaction.emoji) == "▶️" and current_page != pages:
                    current_page += 1
                    await message.edit(embed=contents[current_page - 1])
                    await message.remove_reaction(reaction, user)
                elif str(reaction.emoji) == "◀️" and current_page > 1:
                    current_page -= 1
                    await message.edit(embed=contents[current_page - 1])
                    await message.remove_reaction(reaction, user)

                # removes reactions if the user tries to go forward on the last page or backwards on the first page
                else: await message.remove_reaction(reaction, user)

            # end loop if user doesn't react after x seconds
            except asyncio.TimeoutError:
                await message.delete()
                break

    @commands.command(aliases=['minecraftaddress'])
    async def minecrafturl(self, ctx):
        """
        Shows IP address for server.

        Usage:
            ?ip
            ?address
        """

        await ctx.send(f"Server IP: ||`{backend_functions.get_public_ip()}`||")
        await ctx.send(f"Alternative Address: ||`{slime_vars.server_url}`|| ({backend_functions.ping_url()})")
        lprint(ctx, 'Fetched server address')

    @commands.command(aliases=['websites', 'showlinks', 'usefullinks', 'sites', 'urls'])
    async def links(self, ctx):
        """
        Shows list of useful websites.

        Usage:
            ?links
            ?sites
        """

        embed = discord.Embed(title='Useful Websites :computer:')

        # Creates embed of links from useful_websites dictionary from slime_vars.py.
        for name, url in slime_vars.useful_websites.items():
            embed.add_field(name=name, value=url, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['setchannelid'])
    async def setchannel(self, ctx):
        """Sets channel_id variable, so bot can send messages without ctx."""

        await ctx.send(f"Set `channel_id`: ||{ctx.channel.id}||")
        backend_functions.edit_file('channel_id', ' ' + str(ctx.channel.id), slime_vars.slime_vars_file)

    @commands.command(aliases=['resetchannelid', 'clearchannelid', 'clearchannel'])
    async def resetchannel(self, ctx):
        """Resets channel_id variable to None."""

        await ctx.send("Cleared `channel_id`")
        backend_functions.edit_file('channel_id', ' None', slime_vars.slime_vars_file)

# Adds functions to bot.
for cog in [Other_Games, Basics, Player, Permissions, World, Server, World_Backups, Server_Backups, Bot_Functions]:
    bot.add_cog(cog(bot))

# Disable certain commands depending on if using Tmux, RCON, or subprocess.
if_no_tmux = ['serverstart', 'serverrestart']
if_using_rcon = ['oplist', 'properties', 'rcon', 'onelinemode', 'serverstart', 'serverrestart', 'worldbackupslist', 'worldbackupnew', 'worldbackuprestore', 'worldbackupdelete', 'worldreset',
                 'serverbackupslist', 'serverbackupnew', 'serverbackupdelete', 'serverbackuprestore', 'serverreset', 'serverupdate', 'serverlog']

if slime_vars.server_files_access is False and slime_vars.use_rcon is True:
    for command in if_no_tmux: bot.remove_command(command)

if slime_vars.use_tmux is False:
    for command in if_no_tmux: bot.remove_command(command)

if __name__ == '__main__': bot.run(TOKEN)
