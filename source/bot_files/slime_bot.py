import datetime, asyncio, discord, gzip, sys, os
from discord.ext import commands, tasks
from bot_files.backend_functions import send_command, server_status, lprint
import bot_files.backend_functions as backend
import bot_files.components as components
import slime_vars as slime_vars

__version__ = "7.0"
__date__ = '2022/10/19'
__author__ = "DT"
__email__ = "dt01@pm.me"
__license__ = "GPL 3"
__status__ = "Development"

ctx = 'slime_bot.py'  # For logging. So you know where it's coming from.
# Make sure command_prifex doesn't conflict with other bots.
help_cmd = commands.DefaultHelpCommand(show_parameter_descriptions=False)
bot = commands.Bot(command_prefix=slime_vars.command_prefex, case_insensitive=slime_vars.case_insensitive, intents=slime_vars.intents, help_command=help_cmd)
backend.bot = components.bot = bot

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await setup(bot)

    lprint(ctx, f"Bot PRIMED (v{__version__})")  # Logs event to bot_log.txt.
    await backend.server_status()  # Check server status on bot startup.

    # Will send startup messages to specified channel if given channel_id.
    if slime_vars.channel_id:
        channel = bot.get_channel(slime_vars.channel_id)
        backend.channel_set(channel)  # Needed to set global discord_channel variable for other modules (am i doing this right?).

        await channel.send(f':white_check_mark: v{__version__} **Bot PRIMED** {datetime.datetime.now().strftime("%X")}')
        await channel.send(f'Server: `{slime_vars.server_selected[0]}`')
        # Shows Start/Stop game control panel, Control Panel, and Minecraft status page buttons.
        on_ready_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Buttons', 'buttonspanel', '\U0001F518'], ['Minecraft Status', 'serverstatus', '\U00002139']]
        await channel.send('Use `?cp` for Minecraft Control Panel. `?mstat` Minecraft Status page. `?help`/`help2` for all commands.', view=components.new_buttons(on_ready_buttons))

class Slime_Bot_Commands(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command()
    async def botinfo(self, ctx):
        """Shows bot version and other info."""

        await ctx.send(f"Bot Version: `{__version__}`")

    @commands.command(aliases=['rbot', 'rebootbot', 'botreboot'])
    async def botrestart(self, ctx):
        """Restart this bot."""

        await components.clear()
        await ctx.send("***Rebooting Bot...*** :arrows_counterclockwise: ")
        lprint(ctx, "Restarting bot...")

        if slime_vars.use_subprocess:
            if await server_status():
                await ctx.send("Server is running. Stop server first with `?serverstop`.")

        os.chdir(slime_vars.bot_src_path)
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['botquit'])
    async def botstop(self, ctx):
        """Restart this bot."""

        await ctx.send("**Bot Halted**")
        sys.exit(1)

    @commands.command(aliases=['blog'])
    async def botlog(self, ctx, lines=5):
        """
        Show bot log.

        Args:
            lines optional default(5): Number of most recent lines to show.

        Usage:
            ?botlog - Shows 5 bot log lines
            ?blog 15
        """

        log_data = backend.server_log(file_path=slime_vars.bot_log_file, lines=lines, log_mode=True, return_reversed=True)
        await ctx.send(f"***Fetching {lines} Bot Log...*** :tools:")
        if log_data:
            # Shows server log line by line.
            i = 1
            for line in log_data.split('\n'):
                i += 1
                await ctx.send(f"_({line.split(']', 1)[0][1:]})_ **{line.split(']', 1)[1].split('):', 1)[0][2:]}**: {line.split(']', 1)[1].split('):', 1)[1][1:]}")
            await ctx.send("-----END-----")
            lprint(ctx, f"Fetched Bot Log: {lines}")
        else:
            await ctx.send("**Error:** Problem fetching data. File may be empty or not exist")
            lprint(ctx, "ERROR: Issue getting bog log data.")

    @commands.command(aliases=['updatebot', 'gitupdate'])
    async def botupdate(self, ctx):
        """Gets update from GitHub."""

        await ctx.send("***Updating from GitHub...*** :arrows_counterclockwise:")

        os.chdir(slime_vars.bot_src_path)
        os.system('git pull')

        await ctx.invoke(self.bot.get_command("botrestart"))

    @commands.command()
    async def help2(self, ctx):
        """Shows help page with embed format, using reactions to navigate pages."""

        lprint(ctx, "Fetched help page")
        current_command, embed_page, contents = 0, 1, []
        pages, current_page, page_limit = 8, 1, 10

        def new_embed(page):
            return discord.Embed(title=f'Help Page {page}/{pages} :question:')

        embed = new_embed(embed_page)
        for command in backend.read_csv('command_info.csv'):
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

    @commands.command(aliases=['getip', 'address', 'getaddress', 'serverip', 'serveraddress'])
    async def ip(self, ctx):
        """
        Shows IP address for server.

        Usage:
            ?ip
            ?address
        """

        await ctx.send(f"Server IP: ||`{backend.get_public_ip()}`||")
        await ctx.send(f"Alternative Address: ||`{slime_vars.server_url}`|| ({backend.ping_url()})")
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
        backend.edit_file('channel_id', ' ' + str(ctx.channel.id), slime_vars.slime_vars_file)

    @commands.command(aliases=['resetchannelid', 'clearchannelid', 'clearchannel'])
    async def resetchannel(self, ctx):
        """Resets channel_id variable to None."""

        await ctx.send("Cleared `channel_id`")
        backend.edit_file('channel_id', ' None', slime_vars.slime_vars_file)

class Discord_Components_Funcs(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Control panels
    @commands.command(aliases=['extrapanel', 'hiddenpanel'])
    async def secretpanel(self, ctx):
        """Shhhhhhhh..... secret panel!!!"""

        secret_buttons = [['Kill Players', '_killplayers', '\U00002753'], ['Kill Entities', '_killentities', '\U0001F4A3'],
                          ['Kill Rando', '_killrando', '\U0001F4A5'], ['HADES Protocol', 'hades', '\U0001F480']]
        await ctx.send("**Secret Panel**", view=components.new_buttons(secret_buttons))

        lprint(ctx, 'Opened secret panel')

    @commands.command(hidden=True)
    async def _control_panel_msg(self, ctx):
        """Shows message and bmode to open the control panel."""

        cp_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Status Page', 'serverstatus', '\U00002139']]
        await ctx.send(content='Use `?cp` for Control Panel. `?stats` Server Status page. `?help` for all commands.', view=components.new_buttons(cp_buttons))

    @commands.command(aliases=['player', 'ppanel', 'pp'])
    async def playerpanel(self, ctx, player=''):
        """
        Select player from list (or all, random) and use quick action buttons.

        Args:
            player optional: Provide player to be selected when bringing up panel.

        Usage:
            ?player
            ?player Frogo
        """

        await components.clear()
        components.data('player_selected', 0)

        players = await backend.get_players()  # Gets list of online players
        if not players: players = [["No Players Online"]]  # Shows 'No Player Online' as a list option to notify no players online.

        select_options = [['All Players', '@a'], ['Random Player', '@r']] + [[i, i] for i in players[0]]

        # Sets selection default to player if received 'player' parameter.
        if player:
            select_options += [[player, player, True]]
            components.data('player_selected', player)

        player_selection_panel = await ctx.send("**Player Panel**", view=components.new_selection(select_options, 'player_selected', "Select Player"))

        player_buttons = [['Kill', 'kill player', '\U0001F52A'], ['Clear Inventory', 'clearinventory player', '\U0001F4A5'],
                          ['Location', 'playerlocate player', '\U0001F4CD'], ['Teleport', '_teleport_selected player', '\U000026A1']]
        b1 = await ctx.send('', view=components.new_buttons(player_buttons))

        player_buttons2 = [['Survival', 'gamemode player survival', '\U0001F5E1'], ['Adventure', 'gamemode player adventure', '\U0001F5FA'],
                           ['Creative', 'gamemode player creative', '\U0001F528'], ['Spectator', 'gamemode player spectator', '\U0001F441']]
        b2 = await ctx.send('', view=components.new_buttons(player_buttons2))

        player_buttons3 = [['Reload', 'playerpanel', '\U0001F504'], ['OP', 'opadd player', '\U000023EB'], ['DEOP', 'opremove player', '\U000023EC'],
                          ['Kick', 'kick player', '\U0000274C'], ['Ban', 'ban player', '\U0001F6AB']]
        b3 = await ctx.send('', view=components.new_buttons(player_buttons3))

        components.data('current_components', [*components.data('current_components'), player_selection_panel, b1, b2, b3])
        lprint(ctx, 'Opened player panel')

    @commands.command(aliases=['tpp', 'tpanel', 'tppanel'])
    async def teleportpanel(self, ctx, target=''):
        """
        Select target player and destination player for teleportation. Can also return player.

        Args:
            target optional: Set a target player.

        Usage:
            ?tppanel Steve - Bring up panel with Steve selected for target player.
            ?tpp
        """

        await components.clear()  # Clear out used components, so you don't run into conflicts and issues.

        players = await backend.get_players()  # Get list of online players.

        # Options for selection boxes.
        if players:
            teleport_select_options = [['Random Player', '@r']] + [[i, i] for i in players[0]]
        else: teleport_select_options = [['No Online Players', '_', True]]
        if target: teleport_select_options += [[target, target, True]]

        # Selections updates teleport_selected list, which will be used in _teleport_selected() when bmode clicked.
        select1 = await ctx.send("**Teleport**", view=components.new_selection([['All Players', '@a']] + teleport_select_options, custom_id='teleport_target', placeholder='Target'))
        select2 = await ctx.send('', view=components.new_selection(teleport_select_options, custom_id='teleport_destination', placeholder='Destination'))

        buttons = [['Reload', 'teleportpanel', '\U0001F504'], ['Teleport', '_teleport_selected', '\U000026A1'], ['Return', '_return_selected', '\U000021A9']]
        buttons_msg = await ctx.send('', view=components.new_buttons(buttons))

        components.data('current_components', [*components.data('current_components'), select1, select2, buttons_msg])

    @commands.command(hidden=True)
    async def _teleport_selected(self, ctx, target_player=None):
        """Teleports selected targets from ?teleport command when use Teleport! bmode."""

        if not target_player: target_player = components.data('teleport_target')  # if not provided player param
        await ctx.invoke(self.bot.get_command('teleport'), target_player, components.data('teleport_destination'))

    # ===== Server panel, change server, download logs, restore/delete server and world backups
    @commands.command(aliases=['cp', 'controls', 'panel'])
    async def controlpanel(self, ctx):
        """
        A control panel to control servers, server backups, and world backups.
        """

        await components.clear()

        mode_select_options = [['Buttons', '_update_control_panel buttons', False, 'Show buttons for common actions'],  # label, value, is default, description
                               ['Servers', '_update_control_panel servers', False, 'Change server'],
                               ['Log Files', '_update_control_panel log_files', False, 'Download server log files'],
                               ['World Backups', '_update_control_panel world_backups', False, 'Backups of world folder'],
                               ['Server Backups', '_update_control_panel server_backups', False, 'Backups of server folder']]
        selection_msg = await ctx.send("**Mode**", view=components.new_selection(mode_select_options, 'update_server_panel', 'Select Mode'))

        # Second select menu, world backups, server backups, log files.
        select_options2 = [[' ', '_', False]]
        selection_msg2 = await ctx.send("", view=components.new_selection(select_options2, 'server_panel2', ''))
        # Buttons will update depending on mode.
        buttons_msg = await ctx.send("", view=components.new_buttons([['Reload', 'controlpanel', '\U0001F504']]))
        buttons_msg2 = await ctx.send("", view=components.new_buttons([['Close', '_close_panel', '\U0000274C']]))

        components.data('server_panel_components', {'options': select_options2, 'msg': [selection_msg2, buttons_msg, buttons_msg2], 'pages': [0, 0], 'params': []})
        components.data('current_components', [selection_msg, selection_msg2, buttons_msg, buttons_msg2])
        lprint(ctx, 'Opened server panel')

    @commands.command(hidden=True)
    async def _update_control_panel(self, ctx, mode, buttons_mode='server'):
        """Show select menu of server log files available to download."""

        failed = False  # if failed to update the components
        components.data('second_selected', None)
        spc = components.data('server_panel_components')  # [select options, select msg, bmode msg, current page, total pages]
        total_pages = 1
        buttons1 = [['Reload', 'controlpanel', '\U0001F504'], ['Back', '_update_select_page back', '\U00002B05'], ['Next', '_update_select_page next', '\U000027A1']]
        buttons_select_options = [[['Server Actions', '_update_control_panel buttons server', False, 'Status, start, motd, server server logs, properties, etc'],  # label, value, is default, description
                                   ['Save/Backup Actions', '_update_control_panel buttons backups', False, 'Autosave, save, backup/restore, etc'],
                                   ['Player Actions', '_update_control_panel buttons players', False, 'Player panel, players list, teleport, chat, banlist/whitelisti, OP, etc'],
                                   ['World Actions', '_update_control_panel buttons world', False, 'Weather, time, etc'],
                                   ['Bot/Extra Actions', '_update_control_panel buttons extra', False, 'Bot log, restart bot, set channel, website links, etc']]]

        if mode in 'buttons':
            select_options = buttons_select_options
            buttons1, buttons2, = [['Reload Panel', 'controlpanel', '\U0001F504'], *components.buttons_dict[buttons_mode][0]], components.buttons_dict[buttons_mode][1]
            params = ["**Buttons**", 'update_server_panel', 'Choose what buttons to show']

        elif mode == 'servers':
            select_options, total_pages = backend.group_items(backend.enum_dir(slime_vars.servers_path, 'ds'))
            if not select_options: select_options, total_pages = [[['No Servers', '_', True]]], 1
            buttons2 = [['Select', 'serverlist bmode', '\U0001F446'], ['Info', 'serverinfo bmode', '\U00002139'], ['Edit', 'serveredit interaction', '\U0000270F'],
                       ['Copy', 'servercopy interaction', '\U0001F1E8'], ['New', 'servernew interaction', '\U0001F195'], ['Delete', 'serverdelete bmode', '\U0001F5D1']]
                        #['Download latest .jar', '']]
            params = ["**Servers**", 'second_selected', 'Select Server']

        elif mode == 'world_backups':
            select_options, total_pages = backend.group_items(backend.enum_dir(slime_vars.world_backups_path, 'd', True))
            if not select_options: select_options = [[['No world backups', '_', True]]]
            buttons2 = [['Restore', 'worldbackuprestore bmode', '\U000021A9'], ['Delete', 'worldbackupdelete bmode', '\U0001F5D1'], ['Backup World', 'worldbackupdate', '\U0001F195']]
            params = ["**World Backups**", 'second_selected', 'Select World Backup']

        elif mode == 'server_backups':
            select_options, total_pages = backend.group_items(backend.enum_dir(slime_vars.server_backups_path, 'd', True))
            if not select_options: select_options = [[['No server backups', '_', True]]]
            buttons2 = [['Restore', 'serverrestore bmode', '\U000021A9'], ['Delete', 'serverbackupdelete bmode', '\U0001F5D1'], ['Backup Server', 'serverbackupdate', '\U0001F195']]
            params = ["**Server Backups**", 'second_selected', 'Select Server Backup']

        elif mode == 'log_files':
            select_options, total_pages = backend.group_items(backend.enum_dir(slime_vars.server_log_path, 'f'))
            if not select_options: select_options = [[['No log files', '_', True]]]
            buttons2 = [['Download', '_get_log_file', '\U0001F4BE']]
            params = ["**Log Files**", 'second_selected', 'Select File']

        try:
            new_msg = await spc['msg'][0].edit(content=f"{params[0]} (1/{total_pages})", view=components.new_selection(select_options[0], params[1], params[2]))
            new_msg2 = await spc['msg'][1].edit(content='', view=components.new_buttons(buttons1))
            new_msg3 = await spc['msg'][2].edit(content='', view=components.new_buttons(buttons2))
            spc['options'] = select_options
            spc['msg'] = [new_msg, new_msg2, new_msg3]
            spc['pages'][1] = total_pages
            spc['params'] = params
            components.data('server_panel_components', spc)
        except: failed = True

        if failed:
            await ctx.send("**Error:** Something went wrong with panel.")
            await ctx.invoke(self.bot.get_command('controlpanel'))
        else: lprint(ctx, f'Updated server panel {mode}')

    @commands.command(aliases=['cp2', 'buttons'])
    async def buttonspanel(self, ctx):
        """Shows all the buttons!"""

        for k, v in components.buttons_dict.items():

            await ctx.send(content=k.capitalize(), view=components.new_buttons(v[1]))
            await ctx.send(content='', view=components.new_buttons(v[0]))

    @commands.command(hidden=True)
    async def _close_panel(self, ctx): await components.clear()

    @commands.command(hidden=True)
    async def _get_log_file(self, ctx):
        """Download server log file, also unzips beforehand if it's a .gz file."""

        log_selected = components.data('second_selected')
        if not log_selected: return  # If not log is selected from Discord selection component
        # Unzips file if it's a .gz file. Will delete file afterwards.
        if log_selected.endswith('.gz'):
            with gzip.open(f'{slime_vars.server_log_path}/{log_selected}', 'rb') as f_in:
                # Writes it in the bot source folder, doesn't matter because it'll be deleted.
                with open(log_selected[:-3], 'wb') as f_out: f_out.write(f_in.read())

                try: await ctx.send('', file=discord.File(log_selected[:-3]))
                except: await ctx.send("**ERROR:** Couldn't fetch file for download.")
                else: os.remove(log_selected[:-3])

        else:
            await ctx.send('', file=discord.File(f'{slime_vars.server_log_path}/{log_selected}'))
            lprint(ctx, f"Fetched log file: {log_selected}")

    @commands.command(hidden=True)
    async def _update_select_page(self, ctx, mode):
        """Updates get_log_file() select component with next or previous 25 items, since it can only show 25 at a time."""

        # Gets next 25 items or previous depending on mode parameter.
        spc = components.data('server_panel_components')
        params = spc['params']
        current_page = spc['pages'][0]
        if mode == 'next': current_page += 1
        elif mode == 'back': current_page -= 1
        else: return

        try: new_msg = await spc['msg'][0].edit(content=f"{params[0]} ({current_page+1}/{spc['pages'][1]})",
                                                view=components.new_selection(spc['options'][current_page], params[1], params[2]))
        except: return
        else: spc['pages'][0] = current_page
        spc['msg'][0] = new_msg
        components.data('server_panel_components', spc)

    # ===== Extra
    @commands.command(hidden=True, aliases=['killallplayers', 'kilkillkill', 'killall'])
    async def _killplayers(self, ctx):
        """Kills all online players using '@a' argument."""

        await ctx.send("All players killed!")
        await send_command('kill @a')
        lprint(ctx, 'Killed: All Players')

    @commands.command(hidden=True, aliases=['killeverything', 'killallentities'])
    async def _killentities(self, ctx):
        """Kills all server entities using '@e' argument."""

        await ctx.send("All entities killed!")
        await send_command('kill @e')
        lprint(ctx, 'Killed: All Entities')

    @commands.command(hidden=True, aliases=['killrandom', 'killrandomplayer'])
    async def _killrando(self, ctx):
        """Kills random player using '@r' argument."""

        await ctx.send("Killed random player! :game_die::knife:")
        await send_command('kill @r')
        lprint(ctx, 'Killed: Random Player')

async def setup(bot):
    for i in os.listdir('./cogs'):
        if i.endswith('.py'):
            await bot.load_extension(f"cogs.{i[:-3]}")
    await bot.add_cog(Slime_Bot_Commands(bot))
    await bot.add_cog(Discord_Components_Funcs(bot))

# Disable certain commands depending on if using Tmux, RCON, or subprocess.
if_no_tmux = ['serverstart', 'serverrestart']
if_using_rcon = ['oplist', 'properties', 'rcon', 'onelinemode', 'serverstart', 'serverrestart', 'worldbackupslist', 'worldbackupnew', 'worldbackuprestore', 'worldbackupdelete', 'worldreset',
                 'serverbackupslist', 'serverbackupnew', 'serverbackupdelete', 'serverbackuprestore', 'serverreset', 'serverupdate', 'serverlog']

# Removes certain commands depending on your setup.
if slime_vars.server_files_access is False and slime_vars.use_rcon is True:
    for command in if_no_tmux: bot.remove_command(command)

if slime_vars.use_tmux is False:
    for command in if_no_tmux: bot.remove_command(command)
