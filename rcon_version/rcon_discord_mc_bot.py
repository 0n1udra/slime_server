import discord, asyncio, os, sys, psutil, time, csv, rcon_server_functions
from discord.ext import commands, tasks
from rcon_server_functions import lprint, discord_bot_token_file

# Exits script if no token.
if os.path.isfile(discord_bot_token_file):
    with open(discord_bot_token_file, 'r') as file:
        TOKEN = file.readline()
else: print("Missing Token File:", discord_bot_token_file), exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')

autosave = False # Feature coming soon...

# Sends command to tmux window running server.
def mc_command(command):
    return rcon_server_functions.mc_rcon(command)

def get_server_status():
    return 'java' in (p.name() for p in psutil.process_iter())

def format_args(args, return_empty=False):
    if args:
        return ' '.join(args)
    else:
        if return_empty:
            return ''
        return "No reason given"

# Gets data from json files in same local.
def get_csv(csv_file):
    os.chdir(rcon_server_functions.server_functions_path)
    with open(csv_file) as file: 
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    lprint("Bot PRIMED.")


# ========== Common Server Functions.
@bot.command(aliases=['/', 'command'])
async def server_command(ctx, *args):
    args = format_args(args)
    response = mc_command(f"{args}")
    await ctx.send(f"`{response}`")
    lprint(ctx, "Sent command: " + args)
    time.sleep(1)
    await ctx.invoke(bot.get_command('log'), lines=2)

@bot.command(aliases=['save', 'sa'])
async def server_save(ctx):
    mc_command('save-all')
    await ctx.send("I saved the world!")
    await ctx.send("**NOTE:** This is not the same as making a backup using `?backup`.")
    lprint(ctx, "Saved world.")

@bot.command(aliases=['say', 's'])
async def server_say(ctx, *msg):
    msg = format_args(msg, return_empty=True)
    mc_command('say ' + msg)
    if not msg:
        await ctx.send("Usage exmaple: `?s Hello everyone!`")
    else: await ctx.send("Message circulated to all active players!")
    lprint(ctx, "Server said: {msg}")

@bot.command(aliases=['tell', 'msg', 'whisper', 't'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    mc_command(f"tell {player} {msg}")
    await ctx.send("Communiqué transmitted to: `{player}`.")
    lprint(ctx, f"Messaged {player} : {msg}")

@bot.command(aliases=['list', 'playerlist', 'pl', 'players'])
async def list_players(ctx):
    log_data = mc_command("list")

    log_data = log_data.split(':')
    text = log_data[-2]
    player_data = log_data[-1]
    # If there's no players connected at the moment.
    if player_data == ' \n':
        await ctx.send(text)
    else:
        # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
        players = [f"`{i.strip()[:-4]}`\n" for i in (log_data[-1]).split(',')]
        await ctx.send(text + ':\n' + ''.join(players))
    lprint(ctx, "Fetched player list.")


# ========== Permissions: Ban, Kick, Whitelist, OP, etc
@bot.command(aliases=['kick', 'k'])
async def player_kick(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f'say WARNING | {player} will be ejected from server in 5s | {reason}.')
    time.sleep(5)
    mc_command(f"kick {player}")
    await ctx.send(f"`{player}` is outta here!")
    lprint(ctx, f"Kicked {player}")

@bot.command(aliases=['ban', 'b'])
async def player_ban(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | Banishing {player} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"kick {player}")
    mc_command(f"ban {player} {reason}")
    await ctx.send(f"Dropkicked and exiled: `{player}`.")
    lprint(ctx, f"Banned {player} : {reason}")

@bot.command(aliases=['pardon', 'unban', 'p'])
async def player_pardon(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} has been vindicated! | {reason}.")
    mc_command(f"pardon {player}")
    await ctx.send(f"Cleansed `{player}`.")
    lprint(ctx, f"Pardoned {player} : {reason}")

@bot.command(aliases=['banlist', 'bl', 'blist'])
async def ban_list(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in get_json('banned-players.json')]: 
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)
    lprint(ctx, f"Fetched banned list.")

@bot.command(aliases=['oplist', 'ol', 'ops'])
async def op_list(ctx):
    op_players = [f"`{i['name']}`" for i in get_json('ops.json')]
    await ctx.send('\n'.join(op_players))
    lprint(ctx, f"Fetched server operators list.")

@bot.command(aliases=['opadd'])
async def op_add(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} has become a God! | {reason}")
    mc_command(f"op {player}")
    await ctx.send(f"`{player}` too op now. ||Please nerf soon rito!||")
    lprint(ctx, f"New server op: {player}")

@bot.command(aliases=['opremove'])
async def op_remove(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} fell from grace! | {reason}")
    mc_command(f"deop {player}")
    await ctx.send(f"`{player}` stripped of Godhood!")
    lprint(ctx, f"Removed server op: {player}")

@bot.command(aliases=['top', 'timedop'])
async def op_timed(ctx, player, time_limit=1):
    await ctx.send(f"Granting `{player}` OP status for {time_limit}m!")
    mc_command(f"say INFO | {player} granted God status for {time_limit}m!")
    mc_command(f"op {player}")
    lprint(ctx, f"OP {player} for {time_limit}.")
    time.sleep(time_limit*60)
    await ctx.send(f"Removed `{player}` OP status!")
    mc_command(f"say INFO | {player} is back to being a mortal.")
    mc_command(f"deop {player}")
    lprint(ctx, f"Remove OP {player}")


# ========== Player: gamemode, kill, tp, etc
@bot.command(aliases=['kill', 'assassinate'])
async def player_kill(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | {player} will be EXTERMINATED! | {reason}.")
    mc_command(f'kill {player}')
    await ctx.send(f"`{player}` assassinated!")
    lprint(ctx, f"Killed: {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill', 'dk'])
async def player_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | {player} will self-destruct in {delay}s | {reason}.")
    time.sleep(delay)
    mc_command(f'kill {player}')
    await ctx.send(f"`{player}` soul has been freed.")
    lprint(ctx, f"Delay killed: {player}")

@bot.command(aliases=['tp', 'teleport'])
async def player_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | Flinging {player} towards {target} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"tp {player} {target}")
    await ctx.send(f"`{player}` and {target} touchin real close now.")
    lprint(ctx, f"Teleported {player} to {target}")

@bot.command(aliases=['gamemode', 'gm'])
async def player_gamemode(ctx, player, state, *reason):
    reason = format_args(reason)
    mc_command(f"say {player} now in {state} | {reason}.")
    mc_command(f"gamemode {state} {player}")
    await ctx.send(f"`{player}` is now in `{state}` indefinitely.")
    lprint(ctx, f"Set {player} to: {state}")

@bot.command(aliases=['timedgamemode', 'timedgm', 'tgm'])
async def player_gamemode_timed(ctx, player, state, duration=None, *reason):
    try: duration = int(duration)
    except: 
        await ctx.send("You buffoon, I need a number to set the duration!")
        return

    reason = format_args(reason)
    mc_command(f"say {player} set to {state} for {duration}s | {reason}.")
    await ctx.send(f"`{player}` set to `{state}` for {duration}s, then will revert to survival.")
    mc_command(f"gamemode {state} {player}")
    time.sleep(duration)
    mc_command(f"gamemode survival {player}")
    await ctx.send(f"`{player}` is back to survival.")
    lprint(ctx, f"Set gamemode: {player} for {duration}")


# ========== World weather, time, etc
@bot.command(aliases=['weather'])
async def world_weather(ctx, state, duration=0):
    mc_command(f'weather {state} {duration*60}')
    if duration: 
        await ctx.send(f"I see some `{state}` in the near future.")
    else: await ctx.send(f"Forecast entails `{state}`.")
    lprint(ctx, f"Weather set to: {state} for {duration}")

@bot.command(aliases=['settime', 'time'])
async def world_time(ctx, set_time=None):
    if set_time:
        mc_command(f"time set {set_time}")
        await ctx.send("Time updated!")
    else: await ctx.send("Need time input, like: `12`, `day`")


# ========== Server Start, status, backup, update, etc
@bot.command(aliases=['motd', 'servermessage'])
async def server_motd(ctx, *message):
    if message:
        message = format_args(message)
        rcon_server_functions.edit_properties('motd', message)
        await ctx.send("Message of the day updates!")
    else: await ctx.send(rcon_server_functions.edit_properties('motd')[1])

@bot.command(aliases=['status', 'serverstatus'])
async def server_status(ctx, show_players=True):
    if get_server_status():
        await ctx.send("Server is now __**ACTIVE**__.")
        if show_players:
            await ctx.invoke(bot.get_command('playerlist'))
    else: await ctx.send("Server is __**INACTIVE**__.")
    lprint(ctx, "Fetched server status.")

@bot.command(aliases=['stop', 'deactivate', 'halt'])
async def server_stop(ctx):
    mc_command('say WARNING | Server will halt in 15s!')
    await ctx.send("***Halting in 15s...***")
    time.sleep(10)
    mc_command('say WARNING | 5s left!')
    time.sleep(5)
    mc_command('stop')
    await ctx.send("World Saved. Server __**HALTED**__")
    lprint(ctx, "Stopping server.")

# Restarts this bot script.
@bot.command(aliases=['restartbot', 'rbot', 'rebootbot'])
async def bot_restart(ctx):
    os.chdir(rcon_server_functions.server_functions_path)
    await ctx.send("***Rebooting Bot...***")
    lprint(ctx, "Restarting bot.")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    lprint(ctx, "Fetched help page.")
    current_command, embed_page, contents = 0, 1, []
    pages, current_page, page_limit = 3, 1, 15

    def new_embed(page):
        return discord.Embed(title=f'Help Page {page}/{pages}')

    embed = new_embed(embed_page)
    for command in get_csv(rcon_server_functions.rcon_command_info_file):
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
                await message.edit(embed=contents[current_page -1])
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

bot.run(TOKEN)
