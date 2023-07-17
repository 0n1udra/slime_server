import discord
from discord.ext import commands
from bot_files.backend_functions import send_command, format_args, lprint
import bot_files.backend_functions as backend
from bot_files.extra import convert_to_bytes

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

        command = format_args(command)
        if not await send_command(command): return False

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

        msg = format_args(msg)

        if not msg:
            await ctx.send("Usage: `?s <message>`\nExample: `?s Hello everyone!`")
        else:
            if await send_command('say ' + msg):
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

        msg = format_args(msg)
        if not player or not msg:
            await ctx.send("Usage: `?tell <player> <message>`\nExample: `?ttell MysticFrogo sup hundo`")
            return False

        if not await send_command(f"tell {player} {msg}"): return

        await ctx.send(f"Communiqué transmitted to: `{player}` :mailbox_with_mail:")
        lprint(ctx, f"Messaged {player} : {msg}")

    @commands.command(aliases=['chat', 'playerchat', 'getchat', 'showchat', 'clog'])
    async def chatlog(self, ctx, *args):
        """
        Shows chat log. Does not include whispers.

        Args:
            lines optional default(5): How many log lines to look through. This is not how many chat lines to show.

        Usage:
            ?chat - Shows latest 5 player chat lines from log file.
            ?chat 50 - May take a while to load all 50 lines.
        """

        try:
            lines = int(args[0])
            args = args[1:]
        except: lines = 5

        try: keyword = ' ' .join(args)
        except: keyword = None

        await ctx.send(f"***Loading {lines} Chat Log...*** :speech_left:")

        # Get only log lines that are user chats.
        log_data = backend.server_log(']: <', lines=lines, filter_mode=True, return_reversed=True)

        try: log_data = log_data.strip().split('\n')
        except:
            await ctx.send("**ERROR:** Problem fetching chat logs, there may be nothing to fetch.")
            return False

        # TODO: Possibly able to remove this and use match= in server_log
        # optionally filter out chat lines only with certain keywords.
        log_data = '\n'.join([i for i in log_data if keyword.lower() in i.lower()])
        await ctx.send(file=discord.File(convert_to_bytes(log_data), 'chat_log.log'))
        lprint(ctx, f"Fetched Chat Log: {lines}")

# ========== World: weather, time.
class World(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Weather
    @commands.command(aliases=['weather', 'setweather'])
    async def weatherset(self, ctx, state='', duration=300):
        """
        Set weather.

        Args:
            state: <clear/rain/thunder>: Weather to change to.
            duration optional default(0): Duration in seconds. Defaults to 300 (5min).

        Usage:
            ?weatherset rain - Rain for 300s.
            ?weather thunder 60
        """

        if not state:
            await ctx.send("Usage: `?weather <state> [duration]`\nExample: `?weather rain`")
            return False

        if not await send_command(f'weather {state} {duration}'): return

        await ctx.send(f"Weather set to: **{state.capitalize()}** {'(' + str(duration) + 's)' if duration else ''}")
        lprint(ctx, f"Weather set to: {state.capitalize()} for {duration}s")

    @commands.command(aliases=['enableweather', 'weatherenable'])
    async def weatheron(self, ctx):
        """Enable weather cycle."""

        await send_command(f'gamerule doWeatherCycle true')
        await ctx.send("Weather cycle **ENABLED**")
        lprint(ctx, 'Weather Cycle: Enabled')

    @commands.command(aliases=['disableweather', 'weatherdisable'])
    async def weatheroff(self, ctx):
        """Disable weather cycle."""

        await send_command(f'gamerule doWeatherCycle false')
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

    # ===== Time
    @commands.command(aliases=['time', 'settime'])
    async def timeset(self, ctx, set_time=''):
        """
        Set time.

        Args:
            set_time: Set time either using day|night|noon|midnight or numerically.

        Usage:
            ?timeset day
            ?time 12
        """

        if set_time:
            if not await send_command(f"time set {set_time}"): return
            await ctx.send(f"Time Updated ({set_time})  :clock9:")
        else: await ctx.send("Need time input, like: `12`, `day`")
        lprint(ctx, f"Timed set: {set_time}")

    @commands.command(aliaases=['daytime', 'setday', 'timesetday'])
    async def timeday(self, ctx):
        """Set time to day."""

        await ctx.invoke(self.bot.get_command('timeset'), set_time='0')

    @commands.command(aliases=['nighttime', 'setnight', 'timesetnight'])
    async def timenight(self, ctx):
        """Set time to night."""

        await ctx.invoke(self.bot.get_command('timeset'), set_time='14000')

    @commands.command(aliases=['enabletime', 'timecycleon'])
    async def timeon(self, ctx):
        """Enable day light cycle."""

        await send_command(f'gamerule doDaylightCycle true')
        await ctx.send("Daylight cycle **ENABLED**")
        lprint(ctx, 'Daylight Cycle: Enabled')

    @commands.command(aliases=['diabletime', 'timecycleoff'])
    async def timeoff(self, ctx):
        """Disable day light cycle."""

        await send_command(f'gamerule doDaylightCycle false')
        await ctx.send("Daylight cycle **DISABLED**")
        lprint(ctx, 'Daylight Cycle: Disabled')

async def setup(bot):
    await bot.add_cog(Basics(bot))
    await bot.add_cog(World(bot))
