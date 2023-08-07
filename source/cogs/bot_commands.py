import os
import sys
import gzip
import asyncio

import discord
from discord.ext import commands, tasks

from bot_files.slime_backend import backend
from bot_files.slime_config import __version__, __date__, __author__, config
from bot_files.slime_utils import lprint, file_utils, utils
from bot_files.discord_components import comps, buttons_dict


class Slime_Bot_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Shows player's online and ping info in bot's custom status text.
        if config.get_config('players_custom_status'):
            self.custom_status_task.start()
            lprint(f"Custom status task started (interval: {config.get_config('custom_status_interval')}m)")

    @tasks.loop(seconds=config.get_config('custom_status_interval') * 60)
    async def custom_status_task(self):
        """
        Updates bot's custom status text with online players and ping
        NOTE: Need to set 'enable-query=true' in server.properties for this to work.
        """

        await self.bot.wait_until_ready()
        data = await backend.server_ping_query()
        if not data: return
        # Will show: Playing - X | Ping - X
        await self.bot.change_presence(activity=discord.Activity(name=f"- {data['players']['online']} | Ping - {data['time']}", type=1))

    @commands.command()
    async def botinfo(self, ctx):
        """Shows bot version and other info."""

        await backend.send_msg(f"Bot Version: v{__version__} - {__date__}\nAuthor: {__author__}")

    @commands.command(aliases=['rbot', 'rebootbot', 'botreboot'])
    async def botrestart(self, ctx):
        """Restart this bot."""

        await comps.clear_current_comps()
        await backend.send_msg("***Rebooting Bot...*** :arrows_counterclockwise: ")
        lprint(ctx, "Restarting bot...")

        # If using subprocess, makes sure server is off before restarting bot. Cus, if bot process dies, so does server.
        if config.get_config('server_use_subprocess'):
            if await backend.server_status():
                await backend.send_msg("Server is running. Stop server first with `?serverstop`.")

        os.chdir(config.get_config('bot_source_path'))
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['botquit'])
    async def botstop(self, ctx):
        """Restart this bot."""

        await backend.send_msg("**Bot Halted**")
        sys.exit(1)

    @commands.command(aliases=['blog'])
    async def botlog(self, ctx, lines=20):
        """
        Show bot log.

        Args:
            lines optional default(5): Number of most recent lines to show.

        Usage:
            ?botlog - Shows 5 bot log lines
            ?blog 15
        """

        log_data = [*file_utils.read_file_reverse_generator(config.get_config('bot_log_filepath'), lines=lines)]
        log_data = '\n'.join(reversed(log_data))

        await backend.send_msg(f"***Fetching {lines} Bot Log...*** :tools:")
        if log_data:
            await backend.send_msg(file=discord.File(utils.convert_to_bytes(log_data), 'bot.log'))
            lprint(ctx, f"Fetched Bot Log: {lines}")
        else:
            await backend.send_msg("**Error:** Problem fetching data. File may be empty or not exist")
            lprint(ctx, "ERROR: Issue getting bog log data.")

    @commands.command(aliases=['updatebot', 'gitupdate'])
    async def botupdate(self, ctx):
        """Gets update from GitHub."""

        await backend.send_msg("***Updating from GitHub...*** :arrows_counterclockwise:")

        os.chdir(config.get_config('bot_source_path'))
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
        for command in file_utils.read_csv('command_info.csv'):
            if not command: continue

            embed.add_field(name=command[0], value=f"{command[1]}\n{', '.join(command[2:])}", inline=False)
            current_command += 1
            if not current_command % page_limit:
                embed_page += 1
                contents.append(embed)
                embed = new_embed(embed_page)
        contents.append(embed)

        # getting the message object for editing and reacting
        message = await backend.send_msg(embed=contents[0])
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        # This makes sure nobody except the command sender can interact with the "menu"
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
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

        await backend.send_msg(f"Server IP: ||`{backend.get_public_ip()}`||")
        await backend.send_msg(f"Alternative Address: ||`{config.get_config('server_address')}`|| ({await backend.server_ping()})")
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

        # Creates embed of links from useful_websites dictionary from slime_config.py.
        for name, url in config.get_config('useful_websites').items():
            embed.add_field(name=name, value=url, inline=False)

        await backend.send_msg(embed=embed)


    @commands.command(aliases=['clearmsg', 'clear'])
    async def clearmessages(self, ctx):
        """

        Args:
            ctx:

        Returns:

        """
        await backend.clear_messages()


class Discord_Components_Funcs(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Control panels
    @commands.command(aliases=['extrapanel', 'hiddenpanel'])
    async def secretpanel(self, ctx):
        """Shhhhhhhh..... secret panel!!!"""

        secret_buttons = [['Kill Players', '_killplayers', '\U00002753'], ['Kill Entities', '_killentities', '\U0001F4A3'],
                          ['Kill Rando', '_killrando', '\U0001F4A5'], ['HADES Protocol', 'hades', '\U0001F480']]
        await backend.send_msg("**Secret Panel**", view=comps.new_buttons(secret_buttons))

        lprint(ctx, 'Opened secret panel')

    @commands.command(hidden=True, aliases=['startupmsg'])
    async def bannermsg(self, ctx):
        """Shows useful buttons"""

        on_ready_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Buttons', 'buttonspanel', '\U0001F518'], ['Minecraft Status', 'serverstatus', '\U00002139']]
        await backend.send_msg('Use `?cp` for Minecraft Control Panel. `?mstat` Minecraft Status page. `?help`/`help2` for all commands.', view=comps.new_buttons(on_ready_buttons))

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

        await comps.delete_comps('player_panel')
        comps.set_data('player_selected', 0)

        players = await backend.get_players()  # Gets list of online players
        if not players: players = [["No Players Online"]]  # Shows 'No Player Online' as a list option to notify no players online.

        select_options = [['All Players', '@a'], ['Random Player', '@r']] + [[i, i] for i in players[0]]

        # Sets selection default to player if received 'player' parameter.
        if player:
            select_options += [[player, player, True]]
            comps.set_data('player_selected', player)

        player_selection_panel = await backend.send_msg("**Player Panel**", view=comps.new_selection(select_options, 'player_selected', "Select Player"))

        player_buttons = [
            ['Kill', 'kill player', '\U0001F52A'], ['Clear Inventory', 'clearinventory player', '\U0001F4A5'],
            ['Location', 'playerlocate player', '\U0001F4CD'], ['Teleport', '_teleport_selected player', '\U000026A1'],
            ['Survival', 'gamemode player survival', '\U0001F5E1'], ['Adventure', 'gamemode player adventure', '\U0001F5FA'],
            ['Creative', 'gamemode player creative', '\U0001F528'], ['Spectator', 'gamemode player spectator', '\U0001F441'],
            ['Kick', 'kick player', '\U0000274C'], ['Ban', 'ban player', '\U0001F6AB'],
            ['OP', 'opadd player', '\U000023EB'], ['DEOP', 'opremove player', '\U000023EC'],
            ['Reload', 'playerpanel', '\U0001F504']
        ]

        b1 = await backend.send_msg('', view=comps.new_buttons(player_buttons))

        comps.add_comps('player_panel', [player_selection_panel, b1])
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

        await comps.delete_comps('teleport_panel')  # Clear out used components, so you don't run into conflicts and issues.

        players = await backend.get_players()  # Get list of online players.

        # Options for selection boxes.
        teleport_select_options = [['Random Player', '@r']] + [[i, i] for i in players[0]] if players else [['No Online Players', '_', True]]
        for i in teleport_select_options:
            if target and target.lower() == i[0].lower():
                i.append(True)
                break
            comps.set_data('teleport_target', target)
            comps.set_data('teleport_destination', target)

        # Selections updates teleport_selected list, which will be used in _teleport_selected() when bmode clicked.
        select1 = await backend.send_msg("**Teleport**", view=comps.new_selection([['All Players', '@a']] + teleport_select_options, custom_id='teleport_target', placeholder='Target'))
        select2 = await backend.send_msg('', view=comps.new_selection(teleport_select_options, custom_id='teleport_destination', placeholder='Destination'))

        buttons = [['Reload', 'teleportpanel', '\U0001F504'], ['Teleport', '_teleport_selected', '\U000026A1'], ['Return', '_return_selected', '\U000021A9']]
        buttons_msg = await backend.send_msg('', view=comps.new_buttons(buttons))

        comps.add_comps('teleport_panel', [select1, select2, buttons_msg])

    @commands.command(hidden=True)
    async def _teleport_selected(self, ctx, target_player=None):
        """Teleports selected targets from ?teleport command when use Teleport! bmode."""

        if not target_player: target_player = comps.get_data('teleport_target', '')  # if not provided player param
        await ctx.invoke(self.bot.get_command('teleport'), target_player, comps.get_data('teleport_destination', ''))

    # ===== Bot/server settings, panels, change server, download logs, restore/delete server and world backups
    @commands.command(aliases=['botsettings'])
    async def botconfig(self, ctx): pass

    @commands.command(aliases=['cp', 'controls', 'panel'])
    async def controlpanel(self, ctx):
        """
        A control panel to control servers, server backups, and world backups.
        """

        await comps.clear_current_comps()

        # label, value, is default, description
        mode_select_options = [
            ['Buttons', '_update_control_panel buttons', False, 'Show buttons for common actions'],
            ['Servers', '_update_control_panel servers', False, 'Change server'],
            ['Log Files', '_update_control_panel log_files', False, 'Download server log files'],
            ['World Backups', '_update_control_panel world_backups', False, 'Backups of world folder'],
            ['Server Backups', '_update_control_panel server_backups', False, 'Backups of server folder']
        ]
        selection_msg = await backend.send_msg("**Mode**", view=comps.new_selection(mode_select_options, 'update_server_panel', 'Select Mode'))

        # Second select menu, world backups, server backups, log files.
        select_options2 = [[' ', '_', False]]
        selection_msg2 = await backend.send_msg("", view=comps.new_selection(select_options2, 'server_panel2', ''))
        # Buttons will update depending on mode.
        buttons_msg = await backend.send_msg("", view=comps.new_buttons([['Reload', 'controlpanel', '\U0001F504']]))
        buttons_msg2 = await backend.send_msg("", view=comps.new_buttons([['Close', '_close_panel', '\U0000274C']]))

        comps.set_data('server_panel_components', {'options': select_options2, 'msg': [selection_msg2, buttons_msg, buttons_msg2], 'pages': [0, 0], 'params': []})
        comps.add_comps('current_components', [selection_msg, selection_msg2, buttons_msg, buttons_msg2])
        lprint(ctx, 'Opened server panel')

    @commands.command(hidden=True)
    async def _update_control_panel(self, ctx, mode, buttons_mode='server'):
        """Show select menu of server log files available to download."""

        failed = False  # if failed to update the components, will try to reload components.
        comps.set_data('second_selected', None)
        spc = comps.get_data('server_panel_components')  # [select options, select msg, bmode msg, current page, total pages]
        total_pages = 1
        buttons1 = [['Reload', 'controlpanel', '\U0001F504'], ['Back', '_update_select_page back', '\U00002B05'], ['Next', '_update_select_page next', '\U000027A1']]
        buttons_select_options = [[['Server Actions', '_update_control_panel buttons server', False, 'Status, start, motd, server server logs, properties, etc'],  # label, value, is default, description
                                   ['Save/Backup Actions', '_update_control_panel buttons backups', False, 'Autosave, save, backup/restore, etc'],
                                   ['Player Actions', '_update_control_panel buttons players', False, 'Player panel, players list, teleport, chat, banlist/whitelisti, OP, etc'],
                                   ['World Actions', '_update_control_panel buttons world', False, 'Weather, time, etc'],
                                   ['Bot/Extra Actions', '_update_control_panel buttons extra', False, 'Bot log, restart bot, set channel, website links, etc']]]
        buttons_select_options = [[sublist[:2] + [True] + sublist[3:] if sublist[1].endswith(buttons_mode) else sublist for sublist in buttons_select_options[0]]]

        if mode in 'buttons':
            select_options = buttons_select_options
            buttons1, buttons2, = [['Reload Panel', 'controlpanel', '\U0001F504']], buttons_dict[buttons_mode]
            params = ["**Buttons**", 'update_server_panel', 'Choose what buttons to show']

        elif mode == 'servers':
            select_options, total_pages = utils.group_items(file_utils.enum_dirs_for_discord(config.get_config('servers_path'), 'ds'))
            if not select_options: select_options, total_pages = [[['No Servers', '_', True]]], 1
            buttons2 = [['Select', 'serverselect bmode', '\U0001F446'], ['Info', 'serverinfo bmode', '\U00002139'], ['Edit', 'serveredit interaction', '\U0000270F'],
                        ['Copy', 'servercopy interaction', '\U0001F1E8'], ['New', 'servernew interaction', '\U0001F195'], ['Delete', 'serverdelete bmode', '\U0001F5D1'],
                        ['Update', 'serverupdate', '\U0001F504']]
            params = ["**Servers**", 'second_selected', 'Select Server']

        elif mode == 'world_backups':
            select_options, total_pages = utils.group_items(file_utils.enum_dirs_for_discord(config.get_config('world_backups_path'), 'db'))
            if not select_options: select_options = [[['No world backups', '_', True]]]
            buttons2 = [['Restore', 'worldbackuprestore bmode', '\U000021A9'], ['Delete', 'worldbackupdelete bmode', '\U0001F5D1'], ['Backup World', 'worldbackupdate', '\U0001F195']]
            params = ["**World Backups**", 'second_selected', 'Select World Backup']

        elif mode == 'server_backups':
            select_options, total_pages = utils.group_items(file_utils.enum_dirs_for_discord(config.get_config('server_backups_path'), 'db'))
            if not select_options: select_options = [[['No server backups', '_', True]]]
            buttons2 = [['Restore', 'serverrestore bmode', '\U000021A9'], ['Delete', 'serverbackupdelete bmode', '\U0001F5D1'], ['Backup Server', 'serverbackupdate', '\U0001F195']]
            params = ["**Server Backups**", 'second_selected', 'Select Server Backup']

        elif mode == 'log_files':
            select_options, total_pages = utils.group_items(file_utils.enum_dirs_for_discord(config.get_config('server_logs_path'), 'f'))
            if not select_options: select_options = [[['No log files', '_', True]]]
            buttons2 = [['Download', '_get_log_file', '\U0001F4BE']]
            params = ["**Log Files**", 'second_selected', 'Select File']

        try:
            new_msg = await spc['msg'][0].edit(content=f"{params[0]} (1/{total_pages})", view=comps.new_selection(select_options[0], params[1], params[2]))
            new_msg2 = await spc['msg'][1].edit(content='', view=comps.new_buttons(buttons1))
            new_msg3 = await spc['msg'][2].edit(content='', view=comps.new_buttons(buttons2))
            spc['options'] = select_options
            spc['msg'] = [new_msg, new_msg2, new_msg3]
            spc['pages'][1] = total_pages
            spc['params'] = params
            comps.set_data('server_panel_components', spc)
        except: failed = True

        if failed:
            await backend.send_msg("**Error:** Panel malfunction.")
            await ctx.invoke(self.bot.get_command('controlpanel'))
        else: lprint(ctx, f'Updated server panel {mode}')

    @commands.command(aliases=['buttons', 'b'])
    async def buttonspanel(self, ctx):
        """Shows all the buttons!"""

        await comps.clear_current_comps()
        sserver = config.server_configs
        select_options = [[sserver['server_name'], sserver['server_name'], True, sserver['server_description']]] + [[k, k, False, data['server_description']] for k, data in config.servers.items() if k not in sserver['server_name']]
        server_selection = await backend.send_msg("**Select Server**", view=comps.new_selection(select_options, '_select_server', "Select Server"))

        buttons_components = []
        for k, v in buttons_dict.items():
            # Hides server/world backup commands if there's no local file access.
            if config.get_config('server_files_access') is False and 'backups' in k: continue
            try: buttons_components.append(await backend.send_msg(content=k.capitalize(), view=comps.new_buttons(v)))
            except: pass
        comps.add_comps('buttons_panel', [server_selection, *buttons_components])

    @commands.command(hidden=True)
    async def _close_panel(self, ctx): await comps.clear_current_comps()

    @commands.command(hidden=True)
    async def _get_log_file(self, ctx):
        """Download server log file, also unzips beforehand if it's a .gz file."""

        log_selected = comps.get_data('second_selected')
        if not log_selected: return  # If not log is selected from Discord selection component
        # Unzips file if it's a .gz file. Will delete file afterwards.
        if log_selected.endswith('.gz'):
            with gzip.open(f"{config.get_config('server_logs_path')}/{log_selected}", 'rb') as f_in:
                # Writes it in the bot source folder, doesn't matter because it'll be deleted.
                with open(log_selected[:-3], 'wb') as f_out: f_out.write(f_in.read())

                try: await backend.send_msg('', file=discord.File(log_selected[:-3]))
                except: await backend.send_msg("**ERROR:** Couldn't fetch file for download.")
                else: os.remove(log_selected[:-3])

        else:
            await backend.send_msg('', file=discord.File(f"{config.get_config('server_logs_path')}/{log_selected}"))
            lprint(ctx, f"Fetched log file: {log_selected}")

    @commands.command(hidden=True)
    async def _update_select_page(self, ctx, mode):
        """Discord select component with next or previous 25 items, since it can only show 25 at a time."""

        # Gets next 25 items or previous depending on mode parameter.
        spc = comps.get_data('server_panel_components')
        params = spc['params']
        current_page = spc['pages'][0]
        if mode == 'next': current_page += 1
        elif mode == 'back': current_page -= 1
        else: return

        try: new_msg = await spc['msg'][0].edit(content=f"{params[0]} ({current_page+1}/{spc['pages'][1]})",
                                                view=comps.new_selection(spc['options'][current_page], params[1], params[2]))
        except: return
        else: spc['pages'][0] = current_page
        spc['msg'][0] = new_msg
        comps.set_data('server_panel_components', spc)

    # ===== Extra
    @commands.command(hidden=True, aliases=['killallplayers', 'kilkillkill', 'killall'])
    async def _killplayers(self, ctx):
        """Kills all online players using '@a' argument."""

        await backend.send_msg("All players killed!")
        await backend.send_command('kill @a')
        lprint(ctx, 'Killed: All Players')

    @commands.command(hidden=True, aliases=['killeverything', 'killallentities'])
    async def _killentities(self, ctx):
        """Kills all server entities using '@e' argument."""

        await backend.send_msg("All entities killed!")
        await backend.send_command('kill @e')
        lprint(ctx, 'Killed: All Entities')

    @commands.command(hidden=True, aliases=['killrandom', 'killrandomplayer'])
    async def _killrando(self, ctx):
        """Kills random player using '@r' argument."""

        await backend.send_msg("Killed random player! :game_die::knife:")
        await backend.send_command('kill @r')
        lprint(ctx, 'Killed: Random Player')

async def setup(bot):
    await bot.add_cog(Slime_Bot_Commands(bot))
    await bot.add_cog(Discord_Components_Funcs(bot))
