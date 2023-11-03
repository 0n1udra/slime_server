import os
import sys
import datetime

from discord import Activity, Intents
from discord.ext import commands

from bot_files.slime_backend import backend
from bot_files.slime_config import __version__, config
from bot_files.slime_utils import lprint
from bot_files.discord_components import comps

intents = Intents.default()  # Default: discord.Intents.default()
intents.message_content = True  # Default: True
# Make sure command_prefix doesn't conflict with other bots.
help_cmd = commands.DefaultHelpCommand(show_parameter_descriptions=False)
bot = commands.Bot(command_prefix=config.get_config('command_prefix'), case_insensitive=config.get_config('case_insensitive'), intents=intents, help_command=help_cmd)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await setup(bot)
    await backend.update_bot_object(bot)
    await bot.change_presence(activity=Activity(name=f"- {config.server_configs['server_name']}", type=1))

    lprint(f"Bot PRIMED (v{__version__})")  # Logs event to bot_log.txt.

    # Will send startup messages to specified channel if given channel_id.
    if config.get_config('channel_id'):
        if 'hidebanner' not in sys.argv:
            await backend.send_msg(f':white_check_mark: v{__version__} **Bot PRIMED** {datetime.datetime.now().strftime("%X")}')
            await backend.send_msg(f"Server: `{config.server_configs['server_name']}`")
            # Shows some useful buttons
            on_ready_buttons = [['Control Panel', 'controlpanel', '\U0001F39B'], ['Buttons', 'buttonspanel', '\U0001F518'], ['Minecraft Status', 'serverstatus', '\U00002139']]
            await backend.send_msg('Use `?cp` for Minecraft Control Panel. `?mstat` Minecraft Status page. `?help`/`help2` for all commands.', view=comps.new_buttons(on_ready_buttons))


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


    for command in config.get_config('disabled_commands'):
        bot.remove_command(command)