import os
import sys
import datetime

from discord.ext import commands

from bot_files.slime_backend import backend
from bot_files.slime_config import __version__, config
from bot_files.slime_utils import lprint
from bot_files.discord_components import comps


# Make sure command_prifex doesn't conflict with other bots.
help_cmd = commands.DefaultHelpCommand(show_parameter_descriptions=False)
bot = commands.Bot(command_prefix=config.get_config('command_prefix'), case_insensitive=config.get_config('case_insensitive'), intents=config.intents, help_command=help_cmd)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await setup(bot)
    await backend.update_bot_object(bot)

    lprint(f"Bot PRIMED (v{__version__})")  # Logs event to bot_log.txt.

    # Will send startup messages to specified channel if given channel_id.
    if config.get_config('channel_id'):
        await backend.send_msg(f':white_check_mark: v{__version__} **Bot PRIMED** {datetime.datetime.now().strftime("%X")}')
        if 'hidebanner' not in sys.argv:
            await backend.send_msg(f"Server: `{config.server_configs['server_name']}`")
            # Shows some useful buttons
            on_ready_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Buttons', 'buttonspanel', '\U0001F518'], ['Minecraft Status', 'serverstatus', '\U00002139']]
            await backend.send_msg('Use `?cp` for Minecraft Control Panel. `?mstat` Minecraft Status page. `?help`/`help2` for all commands.', view=comps.new_buttons(on_ready_buttons))

# TODO fix
role_requirements = {
    "my_command1": ["Admin", "Moderator"],
    "my_command2": ["Admin"],
}

@bot.event
async def on_command(ctx):
    def has_custom_role(role_names):
        async def predicate(ctx):
            if any(role.name in role_names for role in ctx.author.roles):
                return True
            raise commands.MissingRole(", ".join(role_names))

        return commands.check(predicate)

    command_name = ctx.command.name
    if command_name in role_requirements:
        required_roles = role_requirements[command_name]
        await has_custom_role(required_roles).predicate(ctx)


@bot.event
async def on_command(ctx):
    backend.set_discord_channel(ctx)

async def setup(bot):
    for i in os.listdir('./cogs'):
        if i.endswith('.py'):
            try:
                await bot.load_extension(f"cogs.{i[:-3]}")
            except commands.ExtensionAlreadyLoaded:
                pass
            except commands.ExtensionNotFound:
                lprint(f"ERROR: Unable to load cog: {i}")
                exit()
            except:
                lprint("ERROR: Error with loading cogs.")
                exit()


