
import discord
from discord.ext import commands, tasks

from bot_files.slime_backend import backend
from bot_files.slime_utils import lprint, utils


# ========== Basics: Say, whisper, online players, server command pass through.
class Basics(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['command', 'mcommand', 'm/'])
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

        command = utils.utils.format_args(command)
        if await backend.send_command(command) is False:
            return False

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

        msg = utils.format_args(msg)

        if not msg:
            await ctx.send("Usage: `?s <message>`\nExample: `?s Hello everyone!`")
        else:
            if await backend.send_command('say ' + msg):
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

        msg = utils.format_args(msg)
        if not player or not msg:
            await ctx.send("Usage: `?tell <player> <message>`\nExample: `?ttell MysticFrogo sup hundo`")
            return False

        if await backend.send_command(f"tell {player} {msg}") is False: return

        await ctx.send(f"Communiqué transmitted to: `{player}` :mailbox_with_mail:")
        lprint(ctx, f"Messaged {player} : {msg}")

    @commands.command(aliases=['chat', 'playerchat', 'getchat', 'showchat', 'clog', 'cl', 'c'])
    async def chatlog(self, ctx, *args):
        """
        Shows chat log. Does not include whispers.

        Args:
            lines optional default(5): How many log lines to look through. This is not how many chat lines to show.

        Usage:
            ?chat - Shows latest 5 lines of chat from log file.
            ?chat 50 - May take a while to load all 50 lines.
            ?c Hello - Only get chat lines containing 'Hello'
            NOTE: ?c 5 hello does not work.
        """

        # Parse line number parameter from input.
        try:
            lines = int(args[0])
            args = args[1:]
        except: lines = 5

        try: keyword = ' ' .join(args)
        except: keyword = None

        await ctx.send(f"***Loading {lines} Chat Log...*** :speech_left:")

        # Get only log lines that are user chats.
        if log_data := await backend.read_server_log(']: <', lines=lines, find_all=True):

            # optionally filter out chat lines only with certain keywords.
            log_data = '\n'.join([i for i in reversed(log_data) if keyword.lower() in i.lower()])
            if log_data:
                await ctx.send(file=discord.File(utils.convert_to_bytes(log_data), 'chat_log.log'))
                lprint(ctx, f"Fetched Chat Log: {lines} {keyword}")
                return
        await ctx.send("**ERROR:** Problem fetching chat logs, there may be nothing to fetch.")


async def setup(bot):
    await bot.add_cog(Basics(bot))
