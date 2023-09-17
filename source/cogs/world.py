from discord.ext import commands

from bot_files.slime_backend import backend
from bot_files.slime_utils import lprint


# ========== World: weather, time.
class World(commands.Cog):
    def __init__(self, bot): self.bot = bot

    # ===== Weather
    @commands.command(aliases=['weather', 'setweather'])
    async def weatherset(self, ctx, state='', duration=0):
        """
        Set weather.

        Args:
            state: <clear/rain/thunder>: Weather to change to.
            duration optional default(0): Duration in seconds. Defaults to random.

        Usage:
            ?weatherset rain - Rain for 300s.
            ?weather thunder 60
        """

        if not state:
            await backend.send_msg("Usage: `?weather <state> [duration]`\nExample: `?weather rain`")
            return False


        if await backend.send_command(f"weather {state} {duration if duration else ''}") is False:
            await backend.send_msg('ERROR: Could not set weather.')
            return

        await backend.send_msg(f"Weather set to: **{state.capitalize()}** {'(' + str(duration) + 's)' if duration else ''}")
        lprint(ctx, f"Weather set to: {state.capitalize()} for {duration}s")

    @commands.command(aliases=['enableweather', 'weatherenable'])
    async def weatheron(self, ctx):
        """Enable weather cycle."""

        await backend.send_command(f'gamerule doWeatherCycle true')
        await backend.send_msg("Weather cycle **ENABLED**")
        lprint(ctx, 'Weather Cycle: Enabled')

    @commands.command(aliases=['disableweather', 'weatherdisable'])
    async def weatheroff(self, ctx):
        """Disable weather cycle."""

        await backend.send_command(f'gamerule doWeatherCycle false')
        await backend.send_msg("Weather cycle **DISABLED**")
        lprint(ctx, 'Weather Cycle: Disabled')

    @commands.command(aliases=['clearweather', 'weathersetclear'])
    async def weatherclear(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='clear')
        lprint(ctx, 'Weather: Clear')

    @commands.command(aliases=['rainweather', 'weathersetrain'])
    async def weatherrain(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='rain')
        lprint(ctx, 'Weather: Rain')

    @commands.command(aliases=['thunderweather', 'weathersetthunder'])
    async def weatherthunder(self, ctx):
        """Set weather to clear."""

        await ctx.invoke(self.bot.get_command('weatherset'), state='thunder')
        lprint(ctx, 'Weather: Thunder')

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
            if await backend.send_command(f"time set {set_time}") is False: return
            await backend.send_msg(f"Time Updated ({set_time})  :clock9:")
        else: await backend.send_msg("Need time input, like: `12`, `day`")
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

        await backend.send_command(f'gamerule doDaylightCycle true')
        await backend.send_msg("Daylight cycle **ENABLED**")
        lprint(ctx, 'Daylight Cycle: Enabled')

    @commands.command(aliases=['diabletime', 'timecycleoff'])
    async def timeoff(self, ctx):
        """Disable day light cycle."""

        await backend.send_command(f'gamerule doDaylightCycle false')
        await backend.send_msg("Daylight cycle **DISABLED**")
        lprint(ctx, 'Daylight Cycle: Disabled')

async def setup(bot):
    await bot.add_cog(World(bot))
