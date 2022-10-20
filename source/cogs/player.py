import asyncio, discord
from discord.ext import commands, tasks
from bot_files.backend_functions import server_command, format_args, server_status, lprint, dc_dict
import bot_files.backend_functions as backend
import slime_vars

# ========== Player: gamemode, kill, tp, etc
class Player(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['p', 'playerlist', 'listplayers', 'list'])
    async def players(self, ctx, *args):
        """Show list of online players."""

        player_list = await backend.get_player_list()
        if player_list is False: return

        await ctx.send("***Fetching Player List...***")
        if not player_list:
            await ctx.send(f"No players online. ¯\_(ツ)_/¯")
        else:
            _player_list = []
            for i in player_list[0]:
                if 'location' in args:
                    player_location = await backend.get_location(i)
                    _player_list.append(f'**{i.strip()}** `{player_location if player_location else "Location N/A"}`\n')
                else: _player_list.append(f'{i.strip()}, ')

            # Combines 'There are X of a max of X players online' text with player names.
            output = player_list[1] + '\n' + ''.join(_player_list)
            if 'location' in args:
                await ctx.send(output)
                await ctx.send("-----END-----")
            else:
                output = output[:-2]  # Removes trailing ','.
                await ctx.send(output)

        lprint(ctx, "Fetched player list")

    @commands.command(aliases=['pl', 'playercoords', 'playerscoords'])
    async def playerlocations(self, ctx):
        """Shows all online player's xyz location."""

        await ctx.invoke(self.bot.get_command('players'), 'location')

    # ===== Kill player
    @commands.command(aliases=['playerkill', 'pk'])
    async def kill(self, ctx, target='', *reason):
        """
        Kill a player.

        Args:
            target: Target player, casing does not matter.
            reason optional: Reason for kill, do not put in quotes.

        Usage:
            ?kill Steve Because he needs to die!
            ?pk Steve
        """

        if not target:
            await ctx.send("Usage: `?kill <player> [reason]`\nExample: `?kill MysticFrogo 5 Because he killed my dog!`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not await server_command(f"say ---WARNING--- {target} will be EXTERMINATED! : {reason}"): return

        await server_command(f'kill {target}')

        await ctx.send(f"`{target}` :gun: assassinated!")
        lprint(ctx, f"Killed: {target}")

    @commands.command(aliases=['delaykill', 'dkill', 'killwait','waitkill'])
    async def killdelay(self, ctx, target='', delay=5, *reason):
        """
        Kill player after time elapsed.

        Args:
            target: Target player.
            delay optional default(5): Wait time in seconds.
            reason optional: Reason for kill.

        Usage:
            ?delayedkill Steve 10 Do I need a reason? - Waits 10s, and sends message.
            ?dkill Steve - Defaults to 5s wait time before kill.
            ?dkill Steve 15 - Waits for 15s instead of the default 5s.
        """

        reason = format_args(reason, return_no_reason=True)
        if not target:
            await ctx.send("Usage: `?killwait <player> <seconds> [reason]`\nExample: `?killwait MysticFrogo 5 Because he took my diamonds!`")
            return False

        if not await server_command(f"say ---WARNING--- {target} will self-destruct in {delay}s : {reason}"): return

        await ctx.send(f"Killing {target} in {delay}s :bomb:")
        await asyncio.sleep(delay)
        await server_command(f'kill {target}')

        await ctx.send(f"`{target}` soul has been freed.")
        lprint(ctx, f"Delay killed: {target}")

    # ===== Teleportation and location
    @commands.command(aliases=['tp'])
    async def teleport(self, ctx, target='', *destination):
        """
        Teleport player to another player.

        Args:
            target optional: Player to teleport.
            destination optional: Destination, player to teleport to or xyz coordinates.
            reason optional: Reason for teleport.

        Usage:
            ?tp - Brings up player teleport panel
            ?tp Steve - Brings up teleport panel with Steve selected
            ?tp Steve 35 -355 355 - Teleport to specific coordinates
            ?tp Jesse Steve - Teleports Jesse to Steve
            ?tp Steve Jesse I wanted to see him - Teleports and shows message.
        """

        target = target.strip()

        # Allows you to teleport to coordinates.
        try: destination = ' '.join(destination)
        except: destination = destination[0]

        # If received nothing or only target parameters, brings up teleport panel.
        if not target or not destination:
            await ctx.invoke(self.bot.get_command('teleportpanel'), target)
            return

        if not await server_command(f"say ---INFO--- Teleporting {target} to {destination} in 5s"): return
        await ctx.send(f"***Teleporting in 5s...***")

        # Saves current coordinates of target player before teleporting them, so they may be returned.
        targets_coords = await backend.get_location(target)
        try: dc_dict('teleport_return', targets_coords.replace(',', ''))
        except: dc_dict('teleport_return', 0)

        # Gets coordinates for target and destination.
        target_info = f'{target} ~ {targets_coords}'
        # Don't try to get coords if using @r.
        if '@r' in destination:
            destination_info = 'Random player'
        else:
            dest_coord = await backend.get_location(destination)
            destination_info = f'{destination}{" ~ " + dest_coord if dest_coord else ""}'

        await asyncio.sleep(5)
        await server_command(f"tp {target} {destination}")

        await ctx.send(f"**Teleported:** `{target_info}` to `{destination_info}` :zap:")
        lprint(ctx, f"Teleported: ({target_info}) to ({destination_info})")

    @commands.command(aliases=['tpreturn', 'tpr', 'return'])
    async def teleportreturn(self, ctx):
        """Returns last teleported player with bot to original location."""

        await ctx.invoke(self.bot.get_command('teleport'), dc_dict('teleport_target'), dc_dict('teleport_return'))

    # ===== Game mode
    @commands.command(aliases=['gm'])
    async def gamemode(self, ctx, player='', mode='', *reason):
        """
        Change player's gamemode.

        Args:
            player: Target player.
            mode: Game mode survival|adventure|creative|spectator.
            reason optional: Reason for gamemode change.

        Usage:
            ?gamemode Steve creative In creative for test purposes.
            ?gm Jesse survival
        """

        if not player or mode not in ['survival', 'creative', 'spectator', 'adventure']:
            await ctx.send(f"Usage: `?gamemode <name> <mode> [reason]`\nExample: `?gamemode MysticFrogo creative`, `?gm R3diculous survival Back to being mortal!`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not await server_command(f"say {player} now in {mode} : {reason}"): return

        await server_command(f"gamemode {mode} {player}")

        await ctx.send(f"`{player}` is now in `{mode.upper()}` indefinitely.")
        lprint(ctx, f"Set {player} to: {mode}")

    @commands.command(aliases=['gamemodetimelimit', 'timedgm', 'gmtimed', 'gmt'])
    async def gamemodetimed(self, ctx, player='', mode='', duration=60, *reason):
        """
        Change player's gamemode for specified amount of seconds, then will change player back to survival.

        Args:
            player: Target player.
            mode: Game mode survival/adventure/creative/spectator. Default is creative for 30s.
            duration optional default(30): Duration in seconds.
            reason optional: Reason for change.

        Usage:
            ?gamemodetimed Steve spectator Steve needs a time out! - 60s of spectator mode.
            ?tgm Jesse adventure 30 - 30s of adventure mode.
        """

        if not player or mode not in ['survival', 'creative', 'spectator', 'adventure']:
            await ctx.send("Usage: `?gamemodetimed <player> <mode> <seconds> [reason]`\nExample: `?gamemodetimed MysticFrogo spectator 120 Needs a time out`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not await server_command(f"say ---INFO--- {player.upper()} set to {mode} for {duration}s : {reason}"): return

        await server_command(f"gamemode {mode} {player}")
        await ctx.send(f"`{player}` set to `{mode}` for `{duration}s` :hourglass:")
        lprint(ctx, f"Set gamemode: {player} for {duration}s")

        await asyncio.sleep(duration)
        await server_command(f"say ---INFO--- Times up! {player} is now back to SURVIVAL.")
        await server_command(f"gamemode survival {player}")
        await ctx.send(f"`{player}` is back to survival.")

    # ===== Inventory
    @commands.command(aliases=['clear'])
    async def clearinventory(self, ctx, target):
        """
        Clears player inventory.

        Args:
            target: Player to clear inventory.

        Usage:
            ?clear Steve
        """

        if not target:
            await ctx.send("Usage: `?clear <player>")
            return False

        if not await server_command(f"say ---WARNING--- {target} will lose everything!"): return

        await server_command(f'clear {target}')

        await ctx.send(f"`{target}` inventory cleared")
        lprint(ctx, f"Cleared: {target}")

    @commands.command(aliases=['playerlocation', 'locateplayer', 'locate', 'location', 'playercoordinates'])
    async def playerlocate(self, ctx, player=''):
        """
        Gets player's location coordinates.

        Args:
            player: Player to get xyz location.

        Usage:
            ?locate Steve
        """

        if location := await backend.get_location(player):
            await ctx.send(f"Located `{player}`: `{location}`")
            lprint(ctx, f"Located {player}: {location}")
            return location

        await ctx.send(f"**ERROR:** Could not get location.")


# ========== Permissions: Ban, whitelist, Kick, OP.
class Permissions(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Ban, kick, whitelist
    @commands.command()
    async def kick(self, ctx, player='', *reason):
        """
        Kick player from server.

        Args:
            player: Player to kick.
            reason optional: Reason for kick.

        Usage:
            ?kick Steve Because he was trolling
            ?kick Jesse
        """

        if not player:
            await ctx.send("Usage: `?kick <player> [reason]`\nExample: `?kick R3diculous Trolling too much`")
            return False

        reason = format_args(reason, return_no_reason=True)
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
            player: Player to ban.
            reason optional: Reason for ban.

        Usage:
            ?ban Steve Player killing
            ?ban Jesse
        """
        if not player:
            await ctx.send("Usage: `?ban <player> [reason]`\nExample: `?ban MysticFrogo Bad troll`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not await server_command(f"say ---WARNING--- Banishing {player} in 5s : {reason}"):
            return

        await asyncio.sleep(5)

        await server_command(f"ban {player} {reason}")

        await ctx.send(f"Dropkicked and exiled: `{player}` :no_entry_sign:")
        lprint(ctx, f"Banned {player} : {reason}")

    @commands.command(aliases=['unban'])
    async def pardon(self, ctx, player='', *reason):
        """
        Pardon (unban) player.

        Args:
            player: Player to pardon.
            reason optional: Reason for pardon.

        Usage:
            ?pardon Steve He has turn over a new leaf.
            ?unban Jesse
        """
        if not player:
            await ctx.send("Usage: `?pardon <player> [reason]`\nExample: `?ban R3diculous He has been forgiven`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not await server_command(f"say ---INFO--- {player} has been vindicated: {reason} :tada:"):return

        await server_command(f"pardon {player}")

        await ctx.send(f"Cleansed `{player}` :flag_white:")
        lprint(ctx, f"Pardoned {player} : {reason}")

    @commands.command(aliases=['bl', 'bans'])
    async def banlist(self, ctx):
        """Show list of current bans."""

        banned_players = ''
        response = await server_command("banlist")
        if not response: return
        log_data = backend.server_log(log_mode=True, stopgap_str=response[1])

        if slime_vars.use_rcon is True:
            if 'There are no bans' in log_data:
                banned_players = 'No exiles!'
            else:
                data = log_data.split(':', 1)
                for line in data[1].split('.'):
                    line = backend.remove_ansi(line)
                    line = line.split(':')
                    reason = backend.remove_ansi(line[-1].strip())  # Sometimes you'll get ansi escape chars in your reason.
                    player = line[0].split(' ')[0].strip()
                    banner = line[0].split(' ')[-1].strip()
                    if len(player) < 2:
                        continue
                    banned_players += f"**{player}** banned by `{banner}` : `{reason}`\n"

                banned_players += data[0].strip() + '.'  # Gets line that says 'There are x bans'.

        else:
            for line in filter(None, log_data.split('\n')):  # Filters out blank lines you sometimes get.
                if 'was banned by' in line:  # finds log lines that shows banned players.
                    # Gets relevant data from current log line, and formats it for Discord output.
                    # E.g. [16:42:53] [Server thread/INFO] [minecraft/DedicatedServer]: Slime was banned by Server: No reason given
                    # Extracts Player name, who banned the player, and the reason.
                    ban_log_line = line.split(':')[-2:]
                    player = ban_log_line[0].split(' ')[1].strip()
                    banner = ban_log_line[0].split(' ')[-1].strip()
                    reason = ban_log_line[-1].strip()
                    banned_players += f"**{player}** banned by `{banner}` : `{reason}`\n"
                elif ']: There are no bans' in line:
                    banned_players = 'No exiled ones!'
                    break

        if not banned_players:
            ctx.send('**ERROR:** Trouble fetching ban list.')
            lprint(ctx, f"ERROR: Fetching ban list")
            return

        await ctx.send(banned_players)
        lprint(ctx, f"Fetched ban list")

    @commands.command(aliases=['wl', 'wlist'])
    async def whitelist(self, ctx, arg='', arg2=''):
        """
        Whitelist commands. Turn on/off, add/remove, etc.

        Args:
            arg: User passed in arguments for whitelist command, see below for arguments and usage.
            arg2 optional: Specify player or to specify more options for other arguments, like enforce for example.

        Discord Args:
            list: Show whitelist, same as if no arguments.
            on/off: Whitelist enable/disable
            reload: Reloads from whitelist.json file.
            add/remove <player>: Player add/remove to whitelist.
            enforce <status/on/off>: Changes 'enforce-whitelist' in server properties file.
                Kicks players that are not on the whitelist when using ?whitelist reload command.
                Server reboot required for enforce-whitelist to take effect.

        Usage:
            ?whitelist list
            ?whitelist on
            ?whitelist reload
            ?whitelist add MysticFrogo
            ?whitelist enforce on
        """

        # Checks if inputted any arguments.
        if not arg: await ctx.send(f"\nUsage Examples: `?whitelist add MysticFrogo`, `?whitelist on`, `?whitelist enforce on`, use `?help whitelist` or `?help2` for more.")

        # Checks if server online.
        if not await server_status(discord_msg=True): return

        # Enable/disable whitelisting.
        if arg.lower() in backend.enable_inputs:
            await server_command('whitelist on')
            await ctx.send("**Whitelist ACTIVE** ")
            lprint(ctx, f"Whitelist: Enabled")
        elif arg.lower() in backend.disable_inputs:
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
                log_data = await server_command('whitelist list')
                log_data = log_data[1]
                log_data = backend.remove_ansi(log_data).split(':')
            else:
                await server_command('whitelist list')
                # Parses log entry lines, separating 'There are x whitelisted players:' from the list of players.
                log_data = backend.server_log('whitelisted players:')
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

        op_players = [f"`{i['name']}`" for i in backend.read_json('ops.json')]
        if op_players:
            await ctx.send(f"**OP List** :scroll:")
            await ctx.send('\n'.join(op_players))
        else: await ctx.send("No players are OP.")

        lprint(ctx, f"Fetched server operators list")

    # ===== OP
    @commands.command(aliases=['op', 'addop'])
    async def opadd(self, ctx, player='', *reason):
        """
        Add server operator (OP).

        Args:
            player: Player to make server operator.
            reason optional: Reason for new OP status.

        Usage:
            ?opadd Steve Testing purposes
            ?opadd Jesse
        """

        if not player:
            await ctx.send("Usage: `?op <player> [reason]`\nExample: `?op R3diculous Need to be a God!`")
            return False

        reason = format_args(reason, return_no_reason=True)
        if not reason: return

        if slime_vars.use_rcon:
            command_success = await server_command(f"op {player}")
            command_success = command_success[0]
        else:
            # Checks if successful op by looking for certain keywords in log.
            response = await server_command(f"op {player}")
            command_success = backend.server_log(player, stopgap_str=response[1])

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
            player: Target player.
            reason optional: Reason for deop.

        Usage:
            ?opremove Steve abusing goodhood.
            ?opremove Jesse
        """

        if not player:
            await ctx.send("Usage: `?deop <player> [reason]`\nExample: `?op MysticFrogo Was abusing God powers!`")
            return False

        reason = format_args(reason, return_no_reason=True)
        command_success = False

        if slime_vars.use_rcon:
            command_success = await server_command(f"deop {player}")
            command_success = command_success[0]
        else:
            if response := await server_command(f"deop {player}"):
                command_success = backend.server_log(player, stopgap_str=response[1])

        if command_success:
            await server_command(f"say ---INFO--- {player} no longer OP : {reason}")
            await ctx.send(f"**Player OP Removed:** `{player}`")
            lprint(ctx, f"Removed server OP: {player}")
        else:
            await ctx.send("**ERROR:** Problem removing OP status.")
            lprint(ctx, f"ERROR: Removing server OP: {player}")

    @commands.command(aliases=['optime', 'opt', 'optimedlimit'])
    async def optimed(self, ctx, player='', time_limit=60, *reason):
        """
        Set player as OP for x seconds.

        Args:
            player: Target player.
            time_limit optional default(60): Time limit in seconds.
            reason optional: Reason to OP

        Usage:
            ?optimed Steve 30 Need to check something real quick.
            ?top jesse 300 - 5min being OP
            ?top Steve - 60s
        """

        if not await server_status(discord_msg=True): return

        if not player:
            await ctx.send("Usage: `?optimed <player> <minutes> [reason]`\nExample: `?optimed R3diculous Testing purposes`")
            return False

        await server_command(f"say ---INFO--- {player} granted OP for {time_limit}m : {reason}")
        await ctx.send(f"***Temporary OP:*** `{player}` for {time_limit}m :hourglass:")
        lprint(ctx, f"Temporary OP: {player} for {time_limit}m")
        await ctx.invoke(self.bot.get_command('opadd'), player, *reason)
        await asyncio.sleep(time_limit)
        await ctx.invoke(self.bot.get_command('opremove'), player, *reason)

async def setup(bot):
    await bot.add_cog(Player(bot))
    await bot.add_cog(Permissions(bot))
