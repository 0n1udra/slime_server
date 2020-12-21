import discord, asyncio, os, sys
from discord.ext import commands, tasks
import server_functions
from server_functions import lprint, use_rcon, format_args, mc_command, mc_status

# Exits script if no token.
if os.path.isfile(server_functions.bot_token_file):
    with open(server_functions.bot_token_file, 'r') as file:
        TOKEN = file.readline()
else:
    print("Missing Token File:", server_functions.bot_token_file)
    exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    lprint("Bot PRIMED.")


# ========== Basics: Say, whisper, online players, server command pass through.
class Basics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['command', '/', 'c'])
    async def server_command(self, ctx, *args):
        """
        Pass command directly to server.

        Args:
            command [str]: Server command, do not include the slash /.

        Usage:
            ?command broadcast Hello Everyone!
            ?/ list

        Note: You will get the latest 2 lines from server output, if you need more use ?log.
        """

        args = format_args(args)
        await mc_command(f"{args}")
        lprint(ctx, "Sent command: " + args)
        await ctx.invoke(self.bot.get_command('serverlog'), lines=2)

    @commands.command(aliases=['broadcast', 's'])
    async def say(self, ctx, *msg):
        """
        Broadcast message to online players.

        Args:
            msg [str]: Message to broadcast.

        Usage:
            ?s Hello World!
        """

        msg = format_args(msg, return_empty=True)
        await mc_command('say ' + msg)
        if not msg:
            await ctx.send("Usage example: `?s Hello everyone!`")
        else:
            await ctx.send("Message circulated to all active players!")
        lprint(ctx, f"Server said: {msg}")

    @commands.command(aliases=['whisper', 't'])
    async def tell(self, ctx, player, *msg):
        """
        Message online player directly.

        Args:
            player <str>: Player name, casing does not matter.
            msg [str]: The message, no need for quotes.

        Usage:
            ?tell Steve Hello there!
            ?t Jesse Do you have diamonds?
        """

        msg = format_args(msg)
        await mc_command(f"tell {player} {msg}")
        await ctx.send(f"Communiqué transmitted to: `{player}`.")
        lprint(ctx, f"Messaged {player} : {msg}")

    @commands.command(aliases=['pl', 'playerlist', 'playerslist', 'listplayers', 'listplayer', 'list'])
    async def players(self, ctx):
        """
        Show list of online players and how many out of server limit.
        """

        response = await mc_command("list")

        if use_rcon:
            log_data = response
        else:
            await asyncio.sleep(1)
            log_data = server_functions.mc_log('players online')

        if not log_data:
            await ctx.send("**ERROR:** Trouble fetching player list.")
            return

        log_data = log_data.split(':')
        text = log_data[-2]
        player_names = log_data[-1]
        # If there's no players active, player_names will still contain some anso escape characters.
        if len(player_names.strip()) < 5:
            await ctx.send(text + '.')
        else:
            # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
            players_names = [f"`{i.strip()[:-4]}`\n" if use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]
            await ctx.send(text + ':\n' + ''.join(players_names))
        lprint(ctx, "Fetched player list.")

    @commands.command(aliases=['chatlog', 'playerchat', 'getchat', 'showchat'])
    async def chat(self, ctx, lines=15):
        """
        Get only user chat lines from server log. Note, does not include whipers.

        Args:
            lines [int:15]: How many log lines to look through. This is not how many chat lines to show.
        """

        await ctx.send(f"***Loading Chat...***")

        log_data = server_functions.mc_log(']: <', lines=lines, filter_mode=True)
        chat_data = []
        for line in log_data.split('\n'):
            try:
                line = line.split(']')
                chat_data.append(str(line[0][1:] + ':' + line[2][1:]))
            except:
                pass

        for line in reversed(chat_data):  # Fixes ordering when chatlines shows in Discord.
            await ctx.send(f"`{line}`")

        lprint(ctx, f"Fetching chat from latest {lines} lines of server log.")


# ========== Player: gamemode, kill, tp, etc
class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['pk', 'playerkill'])
    async def kill(self, ctx, player, *reason):
        """
        Kill a player.

        Args:
            player <str>: Target player, casing does not matter.
            reason [str]: Reason for kill, do not put in quotes.

        Usage:
            ?kill Steve Because he needs to die!
            ?pk Steve
        """

        reason = format_args(reason)
        await mc_command(f"say ---WARNING--- {player} will be EXTERMINATED! : {reason}.")
        await mc_command(f'kill {player}')
        await ctx.send(f"`{player}` assassinated!")
        lprint(ctx, f"Killed: {player}")

    @commands.command(aliases=['delayedkill', 'dk'])
    async def delaykill(self, ctx, player, delay=5, *reason):
        """
        Kill player after time elapsed.

        Args:
            player <str>: Target player.
            delay [int:5]: Wait time in seconds.
            reason [str]: Reason for kill.

        Usage:
            ?delayedkill Steve 5 Do I need a reason?
            ?pk Steve 15
        """

        reason = format_args(reason)
        await mc_command(f"say ---WARNING--- {player} will self-destruct in {delay}s: {reason}.")
        await ctx.send(f"Killing {player} in {delay}s!")

        await asyncio.sleep(delay)

        await mc_command(f'kill {player}')
        await ctx.send(f"`{player}` soul has been freed.")
        lprint(ctx, f"Delay killed: {player}")

    @commands.command(aliases=['tp'])
    async def teleport(self, ctx, player, target, *reason):
        """
        Teleport player to another player.

        Args:
            player <str>: Player to teleport.
            target <str>: Destination, player to teleport to.
            reason [str]: Reason for teleport.

        Usage:
            ?teleport Steve Jesse I wanted to see him
            ?tp Jesse Steve
        """

        reason = format_args(reason)
        await mc_command(f"say ---INFO--- Flinging {player} towards {target} in 5s: {reason}.")
        await asyncio.sleep(5)
        await mc_command(f"tp {player} {target}")
        await ctx.send(f"`{player}` and {target} touchin real close now.")
        lprint(ctx, f"Teleported {player} to {target}")

    @commands.command(alises=['gm'])
    async def gamemode(self, ctx, player, state, *reason):
        """
        Change player's gamemode.

        Args:
            player <str>: Target player.
            state <str>: Game mode survival|adventure|creative|spectator.
            reeason [str]: Optional reason for gamemode change.

        Usage:
            ?gamemode Steve creative In creative for test purposes.
            ?gm Jesse survival
        """

        reason = format_args(reason)
        await mc_command(f"say {player} now in {state}: {reason}.")
        await mc_command(f"gamemode {state} {player}")
        await ctx.send(f"`{player}` is now in `{state}` indefinitely.")
        lprint(ctx, f"Set {player} to: {state}")

    @commands.command(aliases=['gamemodetimed', 'timedgm', 'tgm', 'gmt'])
    async def timedgamemode(self, ctx, player, state='creative', duration=60, *reason):
        """
        Change player's gamemode for specified amount of seconds, then will change player back to survival.

        Args:
            player <str>: Target player.
            state [str:creative]: Game mode survival/adventure/creative/spectator. Default is creative for 30s.
            duration [int:30]: Duration in seconds.
            *reason [str]: Reason for change.

        Usage:
            ?timedgamemode Steve spectator Steve needs a time out!
            ?tgm Jesse adventure Jesse going on a adventure.
        """

        reason = format_args(reason)
        await mc_command(f"say ---INFO--- {player} set to {state} for {duration}s: {reason}.")
        await mc_command(f"gamemode {state} {player}")
        await ctx.send(f"`{player}` set to `{state}` for `{duration}s`, then will revert to survival.")
        lprint(ctx, f"Set gamemode: {player} for {duration}s")

        await asyncio.sleep(duration)

        await mc_command(f"say ---INFO--- Times up! {player} is now back to survival.")
        await mc_command(f"gamemode survival {player}")
        await ctx.send(f"`{player}` is back to survival.")


# ========== Permissions: Ban, Whitelist, Kick, OP.
class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx, player, *reason):
        """
        Kick player from server.

        Args:
            player <str>: Player to kick.
            reason [str]: Optional reason for kick.

        Usage:
            ?kick Steve Because he was trolling
            ?kick Jesse
        """

        reason = format_args(reason)
        await mc_command(f'say ---WARNING--- {player} will be ejected from server in 5s: {reason}.')
        await asyncio.sleep(5)
        await mc_command(f"kick {player}")
        await ctx.send(f"`{player}` is outta here!")
        lprint(ctx, f"Kicked {player}")

    @commands.command(aliases=['exile', 'banish'])
    async def ban(self, ctx, player, *reason):
        """
        Ban player from server.

        Args:
            player <str>: Player to ban.
            reason [str]: Reason for ban.

        Usage:
            ?ban Steve Player killing
            ?ban Jesse
        """

        reason = format_args(reason)
        await mc_command(f"say ---WARNING--- Banishing {player} in 5s: {reason}.")
        await asyncio.sleep(5)
        await mc_command(f"kick {player}")
        await mc_command(f"ban {player} {reason}")
        await ctx.send(f"Dropkicked and exiled: `{player}`.")
        lprint(ctx, f"Banned {player} : {reason}")

    @commands.command(aliases=['unban'])
    async def pardon(self, ctx, player, *reason):
        """
        Pardon (unban) player.

        Args:
            player <str>: Player to pardon.
            reason [str]: Reason for pardon.

        Usage:
            ?pardon Steve He has turn over a new leaf.
            ?unban Jesse
        """

        reason = format_args(reason)
        await mc_command(f"say ---INFO--- {player} has been vindicated: {reason}.")
        await mc_command(f"pardon {player}")
        await ctx.send(f"Cleansed `{player}`.")
        lprint(ctx, f"Pardoned {player} : {reason}")

    @commands.command(aliases=['bl', 'bans'])
    async def banlist(self, ctx):
        """Show list of current bans."""

        # Gets online players, formats output for Discord depending on using RCON or reading from server log.
        banned_players = ''
        response = await mc_command("banlist")

        if use_rcon:
            if 'There are no bans' in response:
                banned_players = 'No exiles!'
            else:
                data = response.split(':', 1)
                for line in data[1].split('.'):
                    line = line.split(':')
                    reason = server_functions.remove_ansi(line[-1].strip())  # Sometimes you'll get ansi escape chars in your reason.
                    player = line[0].split(' ')[0].strip()
                    banner = line[0].split(' ')[-1].strip()
                    banned_players += f"`{player}` banned by `{banner}`: `{reason}`\n"

                banned_players += data[0] + '.'  # Gets line that says 'There are x bans'.

        else:
            if log_data := server_functions.mc_log('banlist'):
                for line in filter(None, log_data.split('\n')):  # Filters out blank lines you sometimes get.
                    print('ok:', line)
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
                    print(ban_log_line)
                    player = ban_log_line[0].split(' ')[1].strip()
                    banner = ban_log_line[0].split(' ')[-1].strip()
                    reason = ban_log_line[-1].strip()
                    banned_players += f"`{player}` banned by `{banner}`: `{reason}`\n"
            else:
                banned_players = '**ERROR:** Trouble fetching ban list.'

        await ctx.send(banned_players)
        lprint(ctx, f"Fetched banned list.")

    @commands.command(aliases=['wl', 'whitel', 'white', 'wlist'])
    async def whitelist(self, ctx, arg=None, arg2=None):
        """
        Whitelist commands, shows list, add, remove, turn off and on, etc.

        Args:
            arg [str:None]: User passed in arguments for whitelist command, see below for arguments and usage.
            player [str:None]: Specify player or to specify more options for other arguments, like enforce for example.

        Usage:
            Usage within Discord without any arguments will show whitelist list, else see below for other examples.
            add <player> : Add player to whitelist.
            remove <player>: Remove player from whitelist.
            on: Activates whitelisting..
            off: Deactivate whitelist.
            reload: Reloads from whitelist.json file.
            enforce <status/on/true/off/false>: Changes 'enforce-whitelist' in server properties file.
                Kicks players that are not on the whitelist when using ?whitelist reload command.
                Server reboot required for enforce-whitelist to take effect.
                Using enforce argument alone will also show current status.
        """

        if arg in ['on', 'true']:
            await mc_command('whitelist on')
            await ctx.send("Whitelist **ACTIVE**.")
            lprint(ctx, f"Whitelist activated.")
        elif arg in ['off', 'false']:
            await mc_command('whitelist off')
            await ctx.send("Whitelist **INACTIVE**.")
            lprint(ctx, f"Whitelist deactivated.")

        elif arg == 'add' and arg2:
            await mc_command(f"whitelist {arg} {arg2}")
            await ctx.send(f"Added `{arg2}` to whitelist.")
            lprint(ctx, f"Added to whitelist: {arg2}")
        elif arg == 'remove' and arg2:
            await mc_command(f"whitelist {arg} {arg2}")
            await ctx.send(f"Removed `{arg2}` from whitelist.")
            lprint(ctx, f"Removed from whitelist: {arg2}")

        elif arg == 'reload':
            await mc_command('whitelist reload')
            await ctx.send("***Reloading Whitelist...***\nIf `enforce-whitelist` property is set to `true`, players not on whitelist will be kicked.")

        elif arg == 'enforce' and arg2 is None:
            await ctx.invoke(self.bot.get_command('property'), 'enforce-whitelist')
            await ctx.send(f"\nUsage examples for enforce: `?whitelist enforce true`, `?whitelist enforce false`.")
        elif arg == 'enforce' and arg2 in ['true', 'on']:
            await ctx.invoke(self.bot.get_command('property'), 'enforce-whitelist', 'true')
        elif arg == 'enforce' and arg2 in ['false', 'off']:
            await ctx.invoke(self.bot.get_command('property'), 'enforce-whitelist', 'false')

        elif arg is None or arg == 'list':
            await mc_command('whitelist list')
            await asyncio.sleep(1)
            # Parses log entry lines, separating 'There are x whitelisted players:' from the list of players.
            log_data = server_functions.mc_log('whitelisted players:').split(':')[-2:]
            # Then, formats player names in Discord `player` markdown.
            players = [f"`{player.strip()}`" for player in log_data[1].split(', ')]
            await ctx.send(f"{log_data[0].strip()}\n{', '.join(players)}")
            lprint(ctx, f"Showing whitelist: {log_data[1]}")

            await ctx.send(f"\nUsage examples: `?whitelist add MysticFrogo`, `?whitelist on`, `?whitelist enforce on`, use `?help` or `?help2` for more.")
        else:
            await ctx.send("Command error.")
            return False

    @commands.command(aliases=['ol', 'ops'])
    async def oplist(self, ctx):
        """
        Show list of current server operators.
        """

        op_players = [f"`{i['name']}`" for i in server_functions.get_json('ops.json')]
        await ctx.send('\n'.join(op_players))
        lprint(ctx, f"Fetched server operators list.")

    @commands.command(aliases=['op'])
    async def opadd(self, ctx, player, *reason):
        """
        Add server operator (OP).

        Args:
            player <str>: Player to make server operator.
            reason [str]: Optional reason for new OP status.

        Usage:
            ?opadd Steve Testing purposes
            ?opadd Jesse
        """

        reason = format_args(reason)
        await mc_command(f"say ---INFO--- {player} has become a God!: {reason}")
        await mc_command(f"op {player}")
        await ctx.send(f"`{player}` too op now. ||Please nerf soon rito!||")
        lprint(ctx, f"New server op: {player}")

    @commands.command(aliases=['oprm', 'rmop', 'deop'])
    async def opremove(self, ctx, player, *reason):
        """
        Remove player OP status (deop).

        Args:
            player <str>: Target player.
            reason [str]: Reason for deop.

        Usage:
            ?opremove Steve abusing goodhood.
            ?opremove Jesse
        """

        reason = format_args(reason)
        await mc_command(f"say ---INFO--- {player} fell from grace!: {reason}")
        await mc_command(f"deop {player}")
        await ctx.send(f"`{player}` stripped of Godhood!")
        lprint(ctx, f"Removed server op: {player}")

    @commands.command(aliases=['optimed', 'top'])
    async def timedop(self, ctx, player, time_limit=1):
        """
        Set player as OP for a set amount of seconds.

        Args:
            player <str>: Target player.
            time_limit [int:1]: Time limit in seconds.

        Usage:
            ?timedop Steve 30 Need to check something real quick.
            ?top jesse 60
        """

        await mc_command(f"say ---INFO--- {player} granted God status for {time_limit}m!")
        await mc_command(f"op {player}")
        await ctx.send(f"Granting `{player}` OP status for {time_limit}m!")
        lprint(ctx, f"OP {player} for {time_limit}.")

        await asyncio.sleep(time_limit * 60)

        await mc_command(f"say ---INFO--- {player} is back to being a mere mortal.")
        await mc_command(f"deop {player}")
        await ctx.send(f"Removed `{player}` OP status!")
        lprint(ctx, f"Remove OP {player}")


# ========== World weather, time.
class World(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sa', 'save-all'])
    async def saveall(self, ctx):
        """Save current world, just sends save-all command to server."""

        await mc_command('save-all')
        await ctx.send("I saved the world!")
        await ctx.send("**NOTE:** This is not the same as making a backup using `?backup`.")
        lprint(ctx, "Saved world.")

    @commands.command(aliases=['weather'])
    async def setweather(self, ctx, state, duration=0):
        """
        Set weather.

        Args:
            state: <clear/rain/thunder>: Weather to change to.
            duration [int:0]: Duration in seconds.

        Usage:
            ?setweather rain
            ?weather thunder 60
        """

        await mc_command(f'weather {state} {duration * 60}')
        if duration:
            await ctx.send(f"I see some `{state}` in the near future.")
        else:
            await ctx.send(f"Forecast entails `{state}`.")
        lprint(ctx, f"Weather set to: {state} for {duration}")

    @commands.command(aliases=['time'])
    async def settime(self, ctx, set_time=None):
        """
        Set time.

        Args:
            set_time [int:None]: Set time either using day|night|noon|midnight or numerically.

        Usage:
            ?settime day
            ?time 12
        """

        if set_time:
            await mc_command(f"time set {set_time}")
            await ctx.send("Time updated!")
        else:
            await ctx.send("Need time input, like: `12`, `day`")
        lprint(ctx, f"Timed set: {set_time}")


# ========== Server: Start, Stop, Status, edit property, server log.
class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['info', 'stat', 'stats'])
    async def status(self, ctx):
        """Shows server active status, version, motd, and online players"""

        embed = discord.Embed(title='Current Server', description=f"Name: {server_functions.server[0]}\nDescription: {server_functions.server[1]}\n")
        if await mc_status() is True:
            await ctx.send("Server is: **ACTIVE**.")
            embed.add_field(name='Status', value=f"**ACTIVE**", inline=False)
        else:
            embed.add_field(name='Status', value=f"**INACTIVE**", inline=False)
        embed.add_field(name='MOTD', value=f"{server_functions.get_mc_motd()}", inline=False)
        embed.add_field(name='Version', value=f"{server_functions.mc_version()}", inline=False)
        embed.add_field(name='Location', value=f"`{server_functions.server_path}`", inline=False)
        embed.add_field(name='Start Command', value=f"`{server_functions.server[2]}`", inline=False)  # Shows server name, and small description.
        await ctx.send(embed=embed)

        await ctx.invoke(self.bot.get_command('players'))
        lprint(ctx, "Fetched server status.")

    @commands.command(aliases=['log'])
    async def serverlog(self, ctx, lines=5):
        """
        Show server log.

        Args:
            lines [int:5]: How many most recent lines to show. Max of 20 lines!

        Usage:
            ?serverlog
            ?log 10
        """
        if lines > 20:
            await ctx.send("Can fetch 20 lines or less.")
            return

        log_data = server_functions.mc_log(lines=lines, log_mode=True)
        await ctx.send(f"`{log_data}`")
        lprint(ctx, f"Fetched {lines} lines from server log.")

    @commands.command()
    async def start(self, ctx):
        """
        Start server.

        Note: Depending on your system, server may take 15 to 40+ seconds to fully boot.
        """

        if await mc_status() is True:
            await ctx.send("Server already **ACTIVE**.")
            return False

        await ctx.send("***Booting Server...***")
        server_functions.mc_start()
        await ctx.send("***Fetching server status in 20s...***")
        await asyncio.sleep(20)
        await ctx.invoke(self.bot.get_command('status'))
        lprint(ctx, "Starting server.")

    @commands.command()
    async def stop(self, ctx, now=None):
        """
        Stop server, gives players 15s warning.

        Args:
            now [str]: Stops server immediately without giving online players 15s warning.

        Usage:
            ?stop
            ?stop now
        """

        if await mc_status() is False:
            await ctx.send("Server already **INACTIVE**.")
            return False

        if 'now' in str(now):
            await mc_command('save-all')
            await mc_command('stop')
        else:
            await mc_command('say ---WARNING--- Server will halt in 15s!')
            await ctx.send("***Halting in 15s...***")
            await asyncio.sleep(10)
            await mc_command('say ---WARNING--- 5s left!')
            await asyncio.sleep(5)
            await mc_command('save-all')
            await mc_command('stop')
        await asyncio.sleep(3)
        await ctx.send("Server **HALTED**.")
        server_functions.mc_subprocess = None
        lprint(ctx, "Stopping server.")

    @commands.command(aliases=['reboot'])
    async def restart(self, ctx, now=None):
        """
        Messages player that the server will restart in 15s, then will stop and startup server.

        Args:
            now [str]: Restarts server immediately without giving online players 15s warning.

        Usage:
            ?restart
            ?reboot now
        """

        lprint(ctx, "Restarting server.")
        await ctx.send("***Restarting...***")
        await ctx.invoke(self.bot.get_command('stop'), now=now)
        await asyncio.sleep(2)
        await ctx.invoke(self.bot.get_command('start'))

    @commands.command(aliases=['property', 'p'])
    async def properties(self, ctx, target_property=None, *value):
        """
        Check or change a server.properties property.

        Note: Passing in 'all' for target property argument (with nothing for value argument) will show all the properties.

        Args:
            target_property [str:None]: Target property to change, must be exact in casing and spelling and some may include a dash -.
            value [str]: New value. For some properties you will need to input a lowercase true or false, and for others you may input a string (quotes not needed).

        Usage:
            ?property motd
            ?property spawn-protection 2
            ?property all
        """

        if target_property is None:
            await ctx.send("Need at least property name, optionally input new value to change property.\nUsage example: `?property motd`, `?property motd Hello World!`")
            return

        if not value:
            value = ''
        else:
            value = ' '.join(value)

        server_functions.edit_properties(target_property, value)
        get_property = server_functions.edit_properties(target_property)
        await asyncio.sleep(1)
        await ctx.send(f"`{get_property[0]}`")
        lprint(ctx, f"Server property: {get_property[0]}")

    @commands.command(aliases=['omode', 'om'])
    async def onlinemode(self, ctx, mode=''):
        """
        Check or enable/disable onlinemode property.

        Args:
            mode <true/false>: Update onlinemode property in server.properties file. Must be in lowercase.

        Usage:
            ?onlinemode true
            ?omode false
        """

        if mode in ['true', 'false', '']:
            await ctx.send(f"`{server_functions.edit_properties('online-mode', mode)[0]}`")
            await ctx.send("**Note:** Server restart required to take effect.")
            lprint(ctx, "Online Mode: " + mode)
        else:
            await ctx.send("Need a true or false argument (in lowercase).")

    @commands.command()
    async def motd(self, ctx, *message):
        """
        Check or Update motd property.

        Args:
            message [str]: New message for message of the day for server. No quotes needed.

        Usage:
            ?motd
            ?motd YAGA YEWY!
        """

        message = format_args(message, return_empty=True)
        if use_rcon:
            response = server_functions.get_mc_motd()
        elif server_functions.server_files_access:
            response = server_functions.edit_properties('motd', message)[1]
        else:
            response = '**ERROR:** Fetching server motd failed.'
        await ctx.send(f"`{response}`")
        lprint("motd: " + response)

    @commands.command()
    async def rcon(self, ctx, state=''):
        """
        Check RCON staatus or enable/disable enable-rcon property.

        Args:
            state <true/false>: Set enable-rcon property in server.properties file, true or false must be in lowercase.

        Usage:
            ?rcon
            ?rcon true
            ?rcon false

        """

        if state in ['true', 'false', '']:
            response = server_functions.edit_properties('enable-rcon', state)
            await ctx.send(f"`{response[0]}`")
        else:
            await ctx.send("Need a true or false argument (in lowercase).")

    @commands.command(aliases=['ver', 'v'])
    async def version(self, ctx):
        """Gets Minecraft server version."""

        response = server_functions.mc_version()
        await ctx.send(f"Current version: `{response}`")
        lprint("Fetched Minecraft server version: " + response)

    @commands.command(aliases=['lversion', 'lver', 'lv'])
    async def latestversion(self, ctx):
        """Gets latest Minecraft server version number from official website."""

        response = server_functions.get_latest_version()
        await ctx.send(f"Latest version: `{response}`")
        lprint("Fetched latest Minecraft server version: " + response)


# ========== World backup/restore functions.
class World_Saves(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['backups', 'worldsaves', 'savedworlds', 'worldbackups', 'ws'])
    async def saves(self, ctx, amount=5):
        """
        Show world folder backups.

        Args:
            amount [int:5]: Number of most recent backups to show.

        Usage:
            ?saves
            ?saves 10
        """

        embed = discord.Embed(title='World Backups')
        worlds = server_functions.fetch_worlds(amount)
        for save in worlds:
            embed.add_field(name=worlds.index(save), value=f"`{save}`", inline=False)

        await ctx.send(embed=embed)
        await ctx.send("Use `?restore <index>` to restore world save.")
        await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
        lprint(ctx, f"Fetched {amount} most recent world saves.")

    @commands.command(aliases=['backupworld', 'worldbackup', 'wb'])
    async def backup(self, ctx, *name):
        """
        Backup current world save folder.

        Args:
            name [str]: Keywords or codename for new save. No quotes needed.

        Usage:
            ?backup everything not on fire
            ?backup Jan checkpoint
        """

        if not name:
            await ctx.send("Hey! I need a name or keywords to make a backup!")
            return False
        name = format_args(name)

        await mc_command(f"say ---INFO--- Standby, world is currently being archived. Codename: {name}")
        await ctx.send("***Saving current world...***")
        await mc_command(f"save-all")
        await asyncio.sleep(5)

        new_backup = server_functions.backup_world(name)
        if new_backup:
            await ctx.send(f"Cloned and archived your world to:\n`{new_backup}`.")
        else:
            await ctx.send("**ERROR:** Problem saving the world! || it's doomed!||")

        await ctx.invoke(self.bot.get_command('saves'))
        lprint(ctx, "New backup: " + new_backup)

    @commands.command(aliases=['restoreworld', 'worldrestore', 'wr'])
    async def restore(self, ctx, index=None, now=None):
        """
        Restore from world backup.

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.

        Args:
            index <int:None>: Get index with ?saves command.
            now [str]: Skip 15s wait to stop server. E.g. ?restore 0 now

        Usage:
            ?restore 3
        """

        try:
            index = int(index)
        except:
            await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
            return False

        fetched_restore = server_functions.get_world_from_index(index)
        lprint(ctx, "World restoring to: " + fetched_restore)
        await ctx.send(f"***Restoring World...*** `{fetched_restore}`")
        await mc_command(f"say ---WARNING--- Initiating jump to save point in 5s!: {fetched_restore}")
        await asyncio.sleep(5)

        if await mc_status() is True:
            await ctx.invoke(self.bot.get_command('stop'), now=now)  # Stops if server is running.

        server_functions.restore_world(fetched_restore)  # Gives computer time to move around world files.
        await asyncio.sleep(3)

        await ctx.invoke(self.bot.get_command('start'))

    @commands.command(aliases=['deleteworld', 'worlddelete', 'wd'])
    async def delete(self, ctx, index):
        """
        Delete a world backup.

        Args:
            index <int>: Get index with ?saves command.

        Usage:
            ?delete 0
        """

        try:
            index = int(index)
        except:
            await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
            return False

        to_delete = server_functions.get_world_from_index(index)
        server_functions.delete_world(to_delete)
        await ctx.send(f"World as been incinerated!")
        await ctx.invoke(self.bot.get_command('saves'))
        lprint(ctx, "Deleted: " + to_delete)

    @commands.command(aliases=['rebirth', 'hades', 'wn'])
    async def newworld(self, ctx):
        """
        Deletes current world save folder (does not touch other server files).

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        await mc_command("say ---WARNING--- Project Rebirth will commence in T-5s!")
        await ctx.send(":fire:**INCINERATED**:fire:")
        await ctx.send("**NOTE:** Next startup will take longer, to generate new world. Also, server settings will be preserved, this does not include data like player's gamemode status, inventory, etc.")

        if await mc_status() is True:
            await ctx.invoke(self.bot.get_command('stop'))

        server_functions.restore_world(reset=True)
        await asyncio.sleep(3)

        await ctx.invoke(self.bot.get_command('start'))
        lprint(ctx, "World Reset.")

    @commands.command(aliases=['serverupdate'])
    async def update(self, ctx):
        """
        Updates server.jar file by downloading latest from official Minecraft website.

        Note: This will not make a backup beforehand, suggest doing so with ?serverbackup command.
        """

        lprint(ctx, "Updating server.jar...")
        await ctx.send("***Updating...***")

        if await mc_status(): await ctx.invoke(self.bot.get_command('stop'))
        await asyncio.sleep(5)

        await ctx.send("***Downloading latest server.jar***")
        server = server_functions.download_new_server()

        if server:
            await ctx.send(f"Downloaded latest version: `{server}`")
            await asyncio.sleep(3)
            await ctx.invoke(self.bot.get_command('start'))
        else:
            await ctx.send("**ERROR:** Updating server failed. Suggest restoring from a backup if updating corrupted any files.")
        lprint(ctx, "Server Updated.")


# ========== Server backup/restore functions.
class Server_Saves(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['selectserver', 'sselect'])
    async def serverselect(self, ctx, name=None):
        if name is None:
            embed = discord.Embed(title='Server List')
            for server in server_functions.server_list.values():
                # Shows server name, description, location, and start command.
                embed.add_field(name=server[0], value=f"Description: {server[1]}\nLocation: `{server_functions.mc_path}/{server_functions.server[0]}`\nStart Command: `{server[2]}`", inline=False)
            await ctx.send(embed=embed)

        else:
            if name in server_functions.server_list.keys():
                server_functions.server = server_functions.server_list[name]
                server_functions.server_path = f"{server_functions.mc_path}/{server_functions.server[0]}"
                await ctx.invoke(self.bot.get_command('status'))
                lprint(ctx, f"Server Selected: {name}")

                with open(f"{server_functions.server_functions_path}/vars.txt", 'w+') as f:
                    f.write(name)


    @commands.command(aliases=['serverbackups', 'savedservers', 'ss'])
    async def serversaves(self, ctx, amount=5):
        """
        Show server backups.

        Args:
            amount [int:5]: How many most recent backups to show.

        Usage:
            ?serversaves
            ?serversaves 10
        """

        embed = discord.Embed(title='Server Backups')
        servers = server_functions.fetch_servers(amount)
        for save in servers:
            embed.add_field(name=servers.index(save), value=f"`{save}`", inline=False)

        await ctx.send(embed=embed)
        await ctx.send("Use `?serverrestore <index>` to restore server.")
        await ctx.send("**WARNING:** Restore will overwrite current server. Make a backup using `?serverbackup <codename>`.")
        lprint(ctx, f"Fetched latest {amount} world saves.")

    @commands.command(aliases=['backupserver', 'serversave', 'saveserver', 'sb'])
    async def serverbackup(self, ctx, *name):
        """
        Create backup of server files (not just world save folder).

        Args:
            name [str]: Keyword or codename for save.

        Usage:
            ?serverbackup Dec checkpoint
        """

        if not name:
            await ctx.send("Hey! I need a name or keywords to make a backup!")
            return False

        name = format_args(name)
        await ctx.send("***Backing Up...***")

        await mc_command(f"save-all")
        await asyncio.sleep(5)
        new_backup = server_functions.backup_server(name)

        if new_backup:
            await ctx.send(f"New backup:\n`{new_backup}`.")
        else:
            await ctx.send("**Error** Saving server failed!")

        await ctx.invoke(self.bot.get_command('serversaves'))
        lprint(ctx, "New backup: " + new_backup)

    @commands.command(aliases=['restoreserver', 'sr'])
    async def serverrestore(self, ctx, index=None, now=None):
        """
        Restore server backup.

        Args:
            index <int:None>: Get index number from ?serversaves command.
            now [str:None]: Stop server without 15s wait.

        Usage:
            ?serverrestore 0
        """

        try:
            index = int(index)
        except:
            await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
            return False

        fetched_restore = server_functions.get_server_from_index(index)
        lprint(ctx, "Server restoring to: " + fetched_restore)
        await ctx.send(f"***Restoring Server...*** `{fetched_restore}`")
        await mc_command(f"say ---WARNING--- Initiating jump to save point in 5s!: {fetched_restore}")
        await asyncio.sleep(5)

        if await mc_status() is True:
            await ctx.invoke(self.bot.get_command('stop'), now=now)

        if server_functions.restore_server(fetched_restore):
            await ctx.send("Server **Restored!**")
        else:
            await ctx.send("**ERROR:** Could not restore server!")

        await asyncio.sleep(3)
        await ctx.invoke(self.bot.get_command('start'))

    @commands.command(aliases=['serverremove', 'serverrm', 'sd'])
    async def serverdelete(self, ctx, index):
        """
        Delete a server backup.

        Args:
            index <int>: Index of server save, get with ?serversaves command.

        Usage:
            ?serverdelete 0
            ?serverrm 5
        """

        try:
            index = int(index)
        except:
            await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
            return False

        to_delete = server_functions.get_server_from_index(index)
        server_functions.delete_server(to_delete)
        await ctx.send(f"Server backup deleted!")
        await ctx.invoke(self.bot.get_command('servers'))
        lprint(ctx, "Deleted: " + to_delete)

    @commands.command(aliases=['resetserver', 'serverreset', 'newserver', 'sn'])
    async def servernew(self, ctx):
        """Deletes all current server files, keeps world and server backups."""

        await mc_command("say ---WARNING--- Resetting server in 5s!")
        await ctx.send("**Resetting Server...**")
        await ctx.send("**NOTE:** Next startup will take longer, to setup server and generate new world. Also `server.properties` file will reset!")

        if await mc_status() is True:
            await ctx.invoke(self.bot.get_command('stop'))
        server_functions.restore_server(reset=True)
        lprint(ctx, "Server Reset.")


# ========== Bot: Restart, botlog, help2.
class Bot_Functions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['rbot', 'rebootbot'])
    async def restartbot(self, ctx, now=None):
        """Restart this bot."""

        await ctx.send("***Rebooting Bot...***")
        lprint(ctx, "Restarting bot.")
        if server_functions.use_subprocess:
            await ctx.invoke(self.bot.get_command("stop"), now=now)
        os.chdir(server_functions.server_functions_path)
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['blog'])
    async def botlog(self, ctx, lines=5):
        """
        Show bot log.

        Args:
            lines [int:5]: Number of most recent lines to show. Max of 20 lines.

        Usage:
            ?botlog
            ?blog 15
        """

        if lines > 20:
            await ctx.send("Can fetch 20 lines or less.")
            return

        log_data = server_functions.mc_log(file_path=server_functions.bot_log_file, lines=lines, log_mode=True)
        await ctx.send(f"`{log_data}`")
        lprint(ctx, f"Fetched {lines} lines from bot log.")

    @commands.command()
    async def help2(self, ctx):
        """Shows help page with embed format, using reactions to navigate pages."""

        lprint(ctx, "Fetched help page.")
        current_command, embed_page, contents = 0, 1, []
        pages, current_page, page_limit = 3, 1, 15

        def new_embed(page):
            return discord.Embed(title=f'Help Page {page}/{pages}')

        embed = new_embed(embed_page)
        for command in server_functions.get_csv('command_info.csv'):
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
                else:
                    await message.remove_reaction(reaction, user)

            # end loop if user doesn't react after x seconds
            except asyncio.TimeoutError:
                await message.delete()
                break

    @commands.command(aliases=['commandhelp', 'mchelp', 'mch', 'mcc', 'commandlist'])
    async def mccommands(self, ctx):
        embed = discord.Embed(title='List of Minecraft server commands for JE.',
                              url='https://minecraft.gamepedia.com/Commands#List_and_summary_of_commands',
                              description='Only JE (Java Edition) commands will work.')
        await ctx.send(embed=embed)


# Adds functions to bot.
cogs = [Basics, Player, Permissions, World, Server, World_Saves, Server_Saves, Bot_Functions]
for i in cogs: bot.add_cog(i(bot))

disabled_commands_rcon = ['oplist', 'start', 'restart', 'saves', 'backup', 'restore', 'delete', 'newworld', 'properties', 'rcon', 'onelinemode',
                          'serversaves', 'serverbackup', 'serverdelete', 'serverrestore', 'serverreset', 'update', 'log']
disabled_commands_tmux = ['start', 'restart']

if server_functions.server_files_access is False:
    for command in disabled_commands_rcon: bot.remove_command(command)
if server_functions.use_tmux is False:
    for command in disabled_commands_tmux: bot.remove_command(command)

if __name__ == '__main__': bot.run(TOKEN)
