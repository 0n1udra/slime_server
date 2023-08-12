import os
import sys
import datetime

from discord import Activity
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
    await bot.change_presence(activity=Activity(name=f"- {config.server_configs['server_name']}", type=1))

    lprint(f"Bot PRIMED (v{__version__})")  # Logs event to bot_log.txt.

    # Will send startup messages to specified channel if given channel_id.
    if config.get_config('channel_id'):
        await backend.send_msg(f':white_check_mark: (v{__version__}) **Bot PRIMED** {datetime.datetime.now().strftime("%X")}')
        if 'hidebanner' not in sys.argv:
            await backend.send_msg(f"Server: `{config.server_configs['server_name']}`")
            # Shows some useful buttons
            on_ready_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Buttons', 'buttonspanel', '\U0001F518'], ['Minecraft Status', 'serverstatus', '\U00002139']]
            await backend.send_msg('Use `?cp` for Minecraft Control Panel. `?mstat` Minecraft Status page. `?help`/`help2` for all commands.', view=comps.new_buttons(on_ready_buttons))

# TODO fix
command_config = {
    'permissions': {
        "admin": ["", "Moderator"],
        "basic_controls": ["Admin"],
    }
}

#@bot.event
async def on_command(ctx):
    # Get the command name from the invoked context
    command_name = ctx.command.name
    print(command_name)

    # Get the allowed roles for the command from the JSON configuration
    allowed_roles = command_config.get('roles', {}).get(command_name, [])

    # Check if the user has any of the allowed roles
    if any(role.name in allowed_roles for role in ctx.author.roles):
        # User has permission, continue with executing the command
        await bot.process_commands(ctx)
    else:
        # User does not have permission, send a message or perform other actions
        await ctx.send('You do not have permission to use this command.')


@bot.event
async def on_command(ctx):
    backend.set_discord_channel(ctx)

async def setup(bot: commands.Bot) -> None:
    """
    Loads all cogs from cogs folder.

    Args:
        bot: Discord bot object
    """

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


