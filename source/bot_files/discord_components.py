from typing import Union, Any, List, Dict

import discord
from discord.ext.commands import Context

from bot_files.slime_backend import backend
from bot_files.slime_config import config


buttons_dict = {
    'server':   [['Status Page', 'serverstatus', '\U00002139'], ['Save World', 'saveall', '\U0001F30E'],
                 ['Start Server', 'serverstart', '\U0001F680'], ['Stop Server', 'serverstop', '\U0001F6D1'], ['Reboot Server', 'serverrestart', '\U0001F501'],
                 ['Server Version', 'serverversion', '\U00002139'], ['MotD', 'motd', '\U0001F4E2'],
                 ['Properties File', 'propertiesall', '\U0001F527'], ['Server Log', 'serverlog', '\U0001F4C3'],
                 ['Connections Log', 'connectionslog', '\U0001F4E1']],
    'backups':  [['Disable Autosave', 'autosaveoff', '\U0001F504'], ['Enable Autosave', 'autosaveon', '\U0001F504'],
                 ['Backup World', 'worldbackupdate', '\U0001F195'], ['Backup Server', 'serverbackupdate', '\U0001F195'],
                 ['World Backups', 'worldbackups', '\U0001F4C1'], ['Server Backups', 'serverbackups', '\U0001F4C1']],
    'players':  [['Player List', 'playerlist', '\U0001F5B1'], ['Chat Log', 'chatlog', '\U0001F5E8'],
                 ['Banned list', 'banlist', '\U0001F6AB'], ['Whitelist', 'whitelist', '\U0001F4C3'],
                 ['OP List', 'oplist', '\U0001F4DC'], ['Player Panel', 'playerpanel', '\U0001F39B'], ['Teleport', 'teleport', '\U000026A1']],
    'world':    [['Rain', 'weatherrain', '\U0001F327'], ['Thunder', 'weatherthunder', '\U000026C8'], ['Clear', 'weatherclear', '\U00002600'],
                 ['Enable Weather', 'weatheron', '\U0001F7E2'], ['Disable Weather', 'weatheroff', '\U0001F534'],
                 ['Day', 'timeday', '\U00002600'], ['Night', 'timenight', '\U0001F319'],
                 ['Enable Time', 'timeon', '\U0001F7E2'], ['Disable Time', 'timeoff', '\U0001F534']],
    'extra':    [['Restart Bot', 'botrestart', '\U0001F501'], ['Bot Log', 'botlog', '\U0001F4C3'], ['Get Address', 'ip', '\U0001F310'],
                 ['Website Links', 'links', '\U0001F517'], ['Clear Messages', 'clearmessages', '\U0001F9F9']]
                }

class Comps:
    def __init__(self):
        # Stores active Discord component message objects, select, buttons, embeds, etc
        self.active_comps = {}
        #  and associating data to make it all work.
        self.comp_data = {'files_panel_component': [], 'teleport_destination': '',
                          'log_select_options': [], 'log_select_page': 0}

    def add_comps(self, key: str, value: List) -> Dict:
        """
        Adds Discord message with component to dict, so they can be deleted later.

        Args:
            key (str): Relevant name for component message(s)
            value (Context): Discord backend.send_msg() context.

        Returns:
            dict: Returns updated comp_data dictionary.
        """

        self.active_comps[key] = value
        return self.active_comps

    def get_comps(self, key) -> Union[Context, None]:
        """
        Get Discord context message of component.

        Args:
            key:

        Returns:
            Context, None: Discord message context or None.
        """
        return self.active_comps.get(key, None)

    async def delete_comps(self, comp_name: str) -> Union[Dict, bool]:
        """
        Deletes a message containing componetns.

        Args:
            comp_name (str): The components to delete.

        Returns:
            dict, bool: Updated active_comps dict. Comps not found.
        """

        if _comps := self.active_comps.pop(comp_name, None):
            for c in _comps:
                try: await c.delete()
                except: pass

            return True

        return False

    async def clear_current_comps(self) -> None:
        """
        Deletes old components to prevent conflicts.
        When certain panels (e.g. worldrestorepanel) are opened, they will be added to current_components list.
        When new panel is opened the old one is deleted.

        Is needed because if you change something with an old panel when a new one is needed, conflicts may happen.
        e.g. Deleting a listing in a selection box.
        """

        for k in list(self.active_comps.keys()):
            await self.delete_comps(k)

    def set_data(self, key: str, value: Any) -> Dict:
        """
        Set data needed for associating discord components.

        Args:
            key: Key.
            value: Value.

        Returns:
            dict: Updated comp_data dict.
        """

        self.comp_data[key] = value
        return self.comp_data

    def get_data(self, key: str, fallback: Any = []) -> Union[Any, None]:
        """
        Returns value from comp_data dict.

        Args:
            key str: Item to get.
            fallback Any: What to return if data not found.

        Returns:
            Value of key. None if not found.
        """

        return self.comp_data.get(key, fallback)

    def new_modal(self, field_args: List, title: str, custom_id: str) -> discord.ui.Modal:
        modal = Discord_Modal(title=title, custom_id=custom_id)

        for field in field_args:
            if field[0] == 'text':
                style = discord.TextStyle.short
                if field[5]: style = discord.TextStyle.long  # If long, default is short
                modal.add_item(discord.ui.TextInput(label=field[1], custom_id=field[2], placeholder=field[3], default=field[4], style=style, required=field[6], max_length=field[7]))
            elif field[0] == 'select':
                pass
            else: continue
        return modal

    def new_buttons(self, buttons_list: List) -> discord.ui.View:
        """Create new discord.ui.View and add buttons, then return said view."""

        view = discord.ui.View(timeout=None)
        for bmode in buttons_list:
            if len(bmode) == 2: bmode.append(None)  # For buttons with no emoji.
            view.add_item(Discord_Button(label=bmode[0], custom_id=bmode[1], emoji=bmode[2]))
        return view

    def new_selection(self, select_options_args: List, custom_id: str, placeholder: str) -> discord.ui.View:
        """Create new discord.ui.View, add Discord_Select and populates options, then return said view."""

        view = discord.ui.View(timeout=None)
        select_options = []

        # Create options for select menu.
        for option in select_options_args:
            if len(option) == 2: option += False, None  # Sets default for 'Default' arg for SelectOption.
            elif len(option) == 3: option.append(None)
            select_options.append(discord.SelectOption(label=option[0], value=option[1], default=option[2], description=option[3]))
        view.add_item(Discord_Select(options=select_options, custom_id=custom_id, placeholder=placeholder))
        return view

    def new_embed(self, fields: List, title: str) -> discord.Embed:
        """Create new Embed, adds fields, returns embed."""

        embed = discord.Embed(title=title)

        for i in fields:
            if len(i) == 2: i.append(False)
            embed.add_field(name=i[0], value=i[1], inline=i[2])
        return embed

    def server_modal_fields(self, server_name: str) -> List[List]:
        if server := config.servers.get(server_name):
            data = server
        else: data = config.example_server_configs.copy()

        # type (text, select), label, custom_id, placeholder, default, style True=long, required, max length
        # Limited to 5 components in modal
        return [['text', 'Server Name', 'server_name', 'Name of new server', data['server_name'], False, True, 50],
                ['text', 'Description', 'server_description', 'Add description', data['server_description'], True, True, 500],
                ['text', 'Server Domain/IP', 'server_address', 'Server domain or IP address', data['server_address'], False, True, 500],
                ['text', 'Launch Command', 'server_launch_command', 'Runtime Launch Command for .jar file', data['server_launch_command'], True, True, 500],
                ['text', 'Wait Time (server startup in seconds)', 'startup_wait_time', 'After starting server, bot will wait before fetching server status and other info.', data['startup_wait_time'], False, True, 10]]

comps = Comps()

class Discord_Modal(discord.ui.Modal):
    def __init__(self, title, custom_id):
        super().__init__(title=title, custom_id=custom_id)

    async def on_submit(self, interaction):
        await interaction.response.defer()
        custom_id = interaction.data['custom_id']

        # Extracts data from fields from modal using component's custom_id as dictionary keys.
        submitted_data = {}
        for i in interaction.data['components']:
            i = i['components'][0]
            submitted_data[i['custom_id']] = i['value']

        # Saves data, so it can be retrieved later by other functions, and calls corresponding function using modal's custom_id.
        comps.set_data(custom_id, submitted_data)
        ctx = await backend.bot.get_context(interaction.message)  # Get ctx from message.
        await ctx.invoke(backend.bot.get_command(custom_id), 'submitted')

class Discord_Select(discord.ui.Select):
    def __init__(self, options, custom_id, placeholder='Choose', min_values=1, max_values=1):
        super().__init__(options=options, custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values)

    async def callback(self, interaction):
        await interaction.response.defer()  # Defer response so not to show failed interaction message.
        custom_id = interaction.data['custom_id']
        value = interaction.data['values'][0].strip()

        comps.set_data(custom_id, value)  # Updates corresponding variables

        if custom_id == 'update_server_panel':
            params = ['']
            try:
                value_split = value.split(' ')
                command, params = value_split[0], value_split[1:]
            except: pass

            ctx = await backend.bot.get_context(interaction.message)  # Get ctx from message.
            await ctx.invoke(backend.bot.get_command(command), *params)

        # Updates selected currently selected server, this is for ?buttonspanel select server component.
        if custom_id == '_select_server':
            await backend.select_server(value)

class Discord_Button(discord.ui.Button):
    """
    Create bmode from received list containing label, custom_id, and emoji.
    Uses custom_id with ctx.invoke to call corresponding function.
    """

    def __init__(self, label, custom_id, emoji=None, style=discord.ButtonStyle.grey):
        super().__init__(label=label, custom_id=custom_id, emoji=emoji, style=style)

    async def callback(self, interaction):

        custom_id = interaction.data['custom_id']

        # Get parameter for use of command being invoke from custom_id. E.g. 'gamemode player survival'
        params = ['']
        try:
            custom_id_split = custom_id.split(' ')
            custom_id, params = custom_id_split[0], custom_id_split[1:]
        except: pass

        # Runs function of same name as bmode's .custom_id variable. e.g. _teleport_selected()
        ctx = await backend.bot.get_context(interaction.message)  # Get ctx from message.
        if params:
            if params[0] == 'player': params[0] = comps.get_data('player_selected')  # Use currently selected player as a parameter
            if params[0] == 'interaction': params[0] = interaction  # Send interaction object
            else: await interaction.response.defer()
            await ctx.invoke(backend.bot.get_command(custom_id), *params)
        else:
            await interaction.response.defer()
            await ctx.invoke(backend.bot.get_command(custom_id))

