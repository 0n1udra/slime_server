import subprocess, asyncio, discord, random, os
from discord.ext import commands, tasks
from bot_files.backend_functions import format_args, lprint
import bot_files.backend_functions as backend
from bot_files.components import new_buttons
import slime_vars

# ========== System commands
async def get_log_lines(ctx, game_name, lines, file_path, **kwargs):
    """Get Log lines from game server logs."""

    # Sets needed parameters for server_log() to work as required.
    log_mode = True
    if 'filter_mode' in kwargs: log_mode = False

    await ctx.send(f"***Getting {lines} {game_name} Log Lines...*** :tools:")
    log_data = backend.server_log(file_path=file_path, lines=lines, return_reversed=True, log_mode=log_mode, **kwargs)
    # Splits by \n and prints line by line in discord markdown, ending with END footer.
    if log_data:
        i = 0
        for line in log_data.split('\n'):
            if line:
                i += 1
                await ctx.send(f"**{i}**: `{line}`")
        await ctx.send("-----END-----")
        lprint(ctx, f"Fetched {game_name} Log: {lines}")

class System(commands.Cog):

    def __init__(self, bot): self.bot = bot

    @commands.command(hidden=True, aliases=['sysreboot', 'sysrestart'])
    async def systemrestart(self, ctx):
        """Restart this bot."""

        await ctx.send("***Rebooting ArcPy...*** :arrows_counterclockwise: ")
        lprint(ctx, "Restarting ArcPy...")

        os.system(f"python3 /home/{slime_vars.user}/git/playground/scripts/powerdown.py --restart slime")

    @commands.command(hidden=True, aliases=['sysoff'])
    async def systempowerdown(self, ctx):
        """System shutdown."""

        await ctx.send("Executed power down script.")
        lprint(ctx, "Executed power down script.")
        os.system(f"python3 /home/{slime_vars.user}/git/playground/scripts/powerdown.py slime")

    @commands.command(hidden=True, aliases=['syslog'])
    async def systemlog(self, ctx, lines=5):
        """Shows ~/system.log."""

        await get_log_lines(ctx, 'system', lines, f'/home/{slime_vars.user}/system.log')

    @commands.command(hidden=True, aliases=['upslog', 'pwrlog'])
    async def powerlog(self, ctx, lines=5):
        """Shows /var/log/pwrstatd.log."""

        await get_log_lines(ctx, 'system', lines, f'/var/log/pwrstatd.log')


# ========== Other Games: Valheim, Project Zomboid
class Other_Games(commands.Cog):
    def __init__(self, bot):
        self.ip_text = f'URL: ||`{slime_vars.server_url}`|| ({backend.ping_url()})\nIP: ||`{backend.get_public_ip()}`|| (Use if URL inactive)'

        # Get valheim password by reading and parsing start_server.sh file.
        vpassword = 'N/A'
        try:
            _line = None
            with open(f'{slime_vars.steam_path}/Valheim dedicated server/start_server.sh', 'r') as f:
                for i in f.readlines():
                    if '-password' in i: _line = i
            vpassword = _line.split(' ')[-1].replace('"', '')
        except: pass

        self.valheim_text = f"{self.ip_text}\nPass: `{vpassword}`"
        self.bot = bot

    @commands.command(aliases=['welcome', 'banner'])
    async def splash(self, ctx):
        """Bot splash/startup message."""

        splash_buttons = [['Start/Stop Servers', 'games', '\U0001F3AE'],
                          ['Control Panel', 'controlpanel', '\U0001F39B']]
        await ctx.send('', view=new_buttons(splash_buttons))

    @commands.command
    async def gameshelp(self, ctx):
        """Custom help command for my setup."""

        await ctx.send("""```
?splash       - Show bot's splash/welcome messages.
?games        - Show start/stop buttons for game.
?info         - Get server address(s) and password(s).

Valheim:
  ?vstart     - Start Valheim Server.
  ?vstop      - Stop server.
  ?vstatus    - Check online status.
  ?vupdate    - Stops server and updates it.
  ?vhelp      - Shows instructions for how to join server.
  ?v/ COMMAND - Send command to vhserver.
    Usage: ?v/ setaccesslevel yeeter admin, ?v/ kickuser yeeter, etc...

Project Zomboid:
  ?zstart     - Start Project Zomboid Server.
  ?zstop      - Stop server.
  ?zstatus    - Check online status.
  ?zsave      - Saves game.
  ?zupdate    - Stops server and updates it.
  ?zlog       - Show X log lines. e.g. ?zlog 25.
  ?z/ COMMAND - Send command to server.

Minecraft:
  ?mstart     - Start Minecraft server. 
  ?mstop      - Stop Minecraft server.
  ?mstatus    - Minecraft server info.
  ?help2      - All Minecraft and slime_bot commands.
```""")
        lprint(ctx, "Show help page")

    @commands.command(aliases=['infopage'])
    async def gameinfo(self, ctx):
        """Shows IP address and other info for my servers."""

        await ctx.send(f"""
{self.ip_text}
Password for Valheim: `{slime_vars.valheim_password}`
""")
        lprint(ctx, "Show info page")

    async def steam_update(self, ctx, game_name, steam_id):
        """Update steam games with steacmd."""

        await ctx.send(f"***Updating {game_name} Server...*** :arrows_counterclockwise: _(may take awhile)_")
        lprint(ctx, f"Updating {game_name}...")

        # Runs command and gets output
        try:
            command_output = subprocess.check_output(
                f'steamcmd +login anonymous +app_update {steam_id} +exit'.split(' ')).decode()
        except:
            await ctx.send(f"Error: Update command error")
            lprint(ctx, "Error: Updating: {game_name}, command error")
            return

        if 'up to date' in command_output:
            await ctx.send(f"**{game_name} already up to date.**")
        elif 'fully installed' in command_output:
            await ctx.send(f"**{game_name} updated.**")
            lprint(ctx, f"{game_name} updated")
        elif 'ERROR' in command_output:
            await ctx.send(f"Error: Trouble updating {game_name}.")
            lprint(ctx, f"Error: Updating {game_name}")
        else:
            await ctx.send(f"Error: Unknown error")
            lprint(ctx, f"Error: Updating {game_name}, Unknown error")

    @commands.command(aliases=['game'])
    async def games(self, ctx):
        """Quickly start/stop games with buttons."""

        game_buttons = [['Start', 'valheimstart'], ['Stop', 'valheimstop'], ['Status', 'valheimstatus'],
                        ['Update', 'valheimupdate']]
        await ctx.send("**Valheim** :axe:", view=new_buttons(game_buttons))

        game_buttons2 = [['Start', 'zomboidstart'], ['Update', 'zomboidupdate'], ['Status', 'zomboidstatus'],
                         ['Stop', 'zomboidstop']]
        await ctx.send("**Zomboid** :zombie:", view=new_buttons(game_buttons2))

        game_buttons3 = [['Start', 'serverstart'], ['Stop', 'serverstop'], ['Status', 'serverstatus'],
                         ['Update', 'serverupdate']]
        await ctx.send("**Minecraft** :pick:", view=new_buttons(game_buttons3))

    # ===== Valheim
    @commands.command(aliases=['vhelp'])
    async def valheimhelp(self, ctx):
        """Shows connect to valheim server instructions with included screenshot."""

        await ctx.invoke(self.bot.get_command("valheimstatus"))
        await ctx.send("Join: Start Game > (pick character) Start > Join Game tab > Join IP (Enter URL or IP)")
        await ctx.send(file=discord.File(rf'{os.path.dirname(os.path.abspath(__file__))}/valheim_info.png'))

    @commands.command(aliases=['v/', 'vcommand'])
    async def valheimcommand(self, ctx, *command):
        """
        Sends command to vhserver.

        Args:
            *command str: Command to send to vhserver script.

        Usage:
            *?v/ details
        """

        command = format_args(command)
        backend.valheim_command(command)
        await ctx.send("Sent Command to vhserver")

        lprint(ctx, "Sent Valheim command: " + command)

    @commands.command(aliases=['vstart', 'startvalheim', 'vlaunch'])
    async def valheimstart(self, ctx):
        """Starts Valheim server."""

        if backend.get_proc('valheim_server.x86_64'):
            await ctx.send(f"Valheim Server **Online**.\n{self.valheim_text}")
        else:
            await ctx.send(
                f"***Launching Valheim Server...*** :rocket:\nPlease wait about 15s before attempting to connect.\n{self.valheim_text}")
            backend.valheim_command(f"cd '{slime_vars.steam_path}/Valheim dedicated server/'")
            backend.valheim_command(f"./start_server.sh")
            lprint(ctx, "Launched Valheim Server")

    @commands.command(aliases=['vstop', 'stopvalheim'])
    async def valheimstop(self, ctx):
        """Stops Valheim server."""

        await ctx.send("**Halted Valheim Server** :stop_sign:")
        backend.valheim_command('C-c')
        lprint(ctx, "Stopped Valheim Server")

    @commands.command(aliases=['vstatus', 'vinfo', 'vstat'])
    async def valheimstatus(self, ctx):
        """Checks valheim server active status using 'vhserver details' command."""
        await ctx.send("***Checking Valheim Server Status...***")

        if backend.get_proc('MainValheimThre'):
            await ctx.send(f"Valheim Server **Online**.\n{self.valheim_text}")
        else:
            await ctx.send("Valheim Server **Offline**.\nUse `?vstart` to launch server.")
        lprint(ctx, 'Checked Valheim Status')

    @commands.command(aliases=['vupdate', 'updatevalheim'])
    async def valheimupdate(self, ctx):
        """Updates Valheim server."""

        if backend.get_proc('valheim_server.x86_64'):
            await ctx.invoke(self.bot.get_command("valheimstop"))
            await ctx.send("***Waiting 15s to make sure server has halted***")
            await asyncio.sleep(15)

        await self.steam_update(ctx, 'Valheim', '896660')

    # ===== Project Zomboid
    @commands.command(aliases=['zcommand', 'z/'])
    async def zomboidcommand(self, ctx, *command):
        """
        Pass command directly to Project Zomboid server.

        Args:
            *command str: Server command, do not include the slash /.

        Usage:
            ?z/ startrain

        Note: Currently no feedback.
        """

        command = format_args(command)
        backend.zomboid_command(f"{command}")
        await asyncio.sleep(1)
        ctx.invoke(self.bot.get_command('zlog'))

        lprint(ctx, "Sent Zomboid command: " + command)

    @commands.command(aliases=['zstart', 'startzomboid'])
    async def zomboidstart(self, ctx):
        """Starts Project Zomboid server."""

        # Checks if server is online first.
        random_number = str(random.random())
        backend.zomboid_command(random_number)
        await asyncio.sleep(1)
        # Get response from reading log if it is online.
        log_data = backend.server_log(random_number,
                                                file_path=f'/home/{slime_vars.user}/Zomboid/server-console.txt')

        if log_data:
            await ctx.send(f"Project Zomboid Server **Online**\n{self.ip_text}")
        else:  # Launches if not online already.
            backend.zomboid_command(f"cd '{slime_vars.steam_path}/Project Zomboid Dedicated Server/'")
            backend.zomboid_command(f'./start-server.sh')
            await ctx.send(
                f"***Launching Project Zomboid Server...*** :rocket:\n{self.ip_text}\nPlease wait about 30s before attempting to connect.")
        lprint(ctx, "Launching Project Zomboid Server")

    @commands.command(aliases=['zstop', 'stopzomboid'])
    async def zomboidstop(self, ctx):
        """Stops Project Zomboid server."""

        backend.zomboid_command('quit')
        await ctx.send("**Halted Project Zomboid Server** :stop_sign:")

        lprint(ctx, "Project Zomboid Stopped")

    @commands.command(aliases=['zsave', 'savezomboid'])
    async def zomboidsave(self, ctx):
        """Save Project Zomboid."""

        backend.zomboid_command('save')
        await ctx.send("World Saved")

        lprint(ctx, "Saved Project Zomboid")

    @commands.command(aliases=['zstatus', 'statuszomboid', 'zstat'])
    async def zomboidstatus(self, ctx):
        """Checks valheim server active status using 'vhserver details' command."""

        await ctx.send("***Checking Project Zomboid Server Status...***")

        random_number = str(random.random())
        backend.zomboid_command(random_number)
        await asyncio.sleep(1)
        log_data = backend.server_log(random_number, file_path=f'/home/{slime_vars.user}/Zomboid/server-console.txt')
        if log_data:
            await ctx.send(f"Project Zomboid Server **Online**.\n{self.ip_text}")
        else:
            await ctx.send("Project Zomboid Server **Offline**.\nUse `?zstart` to launch server.")
        lprint(ctx, 'Checked Zomboid Status')

    @commands.command(aliases=['zupdate', 'updatezomboid'])
    async def zomboidupdate(self, ctx):
        """Updates Zomboid server."""

        if backend.get_proc('zomboid'):
            await ctx.invoke(self.bot.get_command("zomboidstop"))
            await ctx.send("_Waiting 15s to make sure server has halted_")
            await asyncio.sleep(15)

        await self.steam_update(ctx, 'Zomboid', '380870')

    @commands.command(aliases=['zlog'])
    async def zomboidlog(self, ctx, lines=5):
        """Show Project Zomboid log lines."""

        await get_log_lines(ctx, 'Zomboid', lines, f'/home/{slime_vars.user}/Zomboid/server-console.txt')

async def setup(bot):
    await bot.add_cog(System(bot))
    await bot.add_cog(Other_Games(bot))
