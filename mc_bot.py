import discord, asyncio, os, psutil, time, json, csv, datetime, mc_funcs
from discord.ext import commands, tasks

mc_server_dir = '/mnt/c/Users/DT/Desktop/MC/server'

# Exits script if no token.
with open('/home/slime/mc_bot_token.txt', 'r') as file: TOKEN = file.readline()
if not TOKEN: print("Token Error."), exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')

# Logging .
def lprint(msg): print(f'{datetime.datetime.today()} | {msg}')

# Sends command to tmux window running server.
async def mc_command(command): os.system(f'tmux send-keys -t mcserver:1.0 "{command}" ENTER')

def format_args(args):
    if args: return ' '.join(args)
    else: return "No reason given"

# Gets data from json files in same local.
def get_json(json_file):
    os.chdir(os.getcwd())
    with open(mc_server_dir + '/' + json_file) as file: 
        return [i for i in json.load(file)]

def get_csv(csv_file):
    os.chdir(os.getcwd())
    with open(csv_file) as file: 
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    lprint("Bot PRIMED.")

# ========== Common Server Functions.
@bot.command(aliases=['save', 'sa'])
async def server_save(ctx):
    await mc_command('/save-all')
    await ctx.send("I saved the world!.")
    lprint("Saved world.")

@bot.command(aliases=['say', 's'])
async def server_say(ctx, *msg):
    msg = format_args(msg)
    await mc_command('/say ' + msg)
    await ctx.send("Message circulated to all active players!")
    lprint("Server said: {msg}")

@bot.command(aliases=['tell', 'msg', 'whisper', 't'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    await mc_command(f"/tell {player} {msg}")
    await ctx.send("Communiqué transmitted to: {player}.")
    lprint(f"Messaged {player} : {msg}")


# ========== Permissions: Ban, Kick, Whitelist, OP, etc
@bot.command(aliases=['kick', 'k'])
async def server_kick(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f'/say WARNING | {player} will be ejected from server in 5s | Reason: {reason}.')
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await ctx.send(f"{player} is outta here!")
    lprint(f"Kicked {player}")

@bot.command(aliases=['ban', 'b'])
async def server_ban(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | Banishing {player} in 5s | Reason: {reason}.")
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await mc_command(f"/ban {player} {reason}")
    await ctx.send(f"Dropkicked and exiled {player}.")
    lprint(f"Banned {player} : {reason}")

@bot.command(aliases=['pardon', 'unban', 'p'])
async def server_pardon(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} has been vindicated | Reason: {reason}.")
    await mc_command(f"/pardon {player}")
    await ctx.send(f"Cleansed {player}.")
    lprint(f"Pardoned {player} : {reason}")

@bot.command(aliases=['banlist', 'bl', 'blist'])
async def server_ban_list(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in get_json('banned-players.json')]: 
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)
    lprint(f"Fetching banned list.")

@bot.command(aliases=['oplist', 'ol', 'ops'])
async def server_op_list(ctx):
    op_players = [f"`{i['name']}`" for i in get_json('ops.json')]
    await ctx.send('\n'.join(op_players))
    lprint(f"Fetching server operators list.")

@bot.command(aliases=['opadd'])
async def server_op_add(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} has become a God | Reason: {reason}")
    await mc_command(f"/op {player}")
    await ctx.send(f"{player} too op now, please nerf soon rito.")
    lprint(f"New server op: {player}")

@bot.command(aliases=['opremove'])
async def server_op_remove(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} fell from grace | Reason: {reason}")
    await mc_command(f"/deop {player}")
    await ctx.send(f"{player} stripped of Godhood!")
    lprint(f"Removed server op: {player}")


# ========== Player: gamemode, kill, tp, etc
@bot.command(aliases=['kill', 'assassinate'])
async def player_kill(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | {player} will be EXTERMINATED | Reason: {reason}.")
    await mc_command(f'/kill {player}')
    await ctx.send("{player} assassinated!")
    lprint(f"Killed: {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill', 'dk'])
async def player_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | {player} will self-destruct in {delay}s | Reason: {reason}.")
    time.sleep(delay)
    await mc_command(f'/kill {player}')
    await ctx.send(f"{player} soul has been freed.")
    lprint(f"Delay killed: {player}")

@bot.command(aliases=['tp', 'teleport'])
async def player_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | Flinging {player} towards {target} in 5s | Reason: {reason}.")
    time.sleep(5)
    await mc_command(f"/tp {player} {target}")
    await ctx.send(f"{player} and {target} touchin real close now.")
    lprint(f"Teleported {player} to {target}")

@bot.command(aliases=['gamemode', 'gm'])
async def player_gamemode(ctx, player, state, *reason):
    reason = format_args(reason)
    await mc_command(f"/say {player} now set to {state} | Reason: {reason}.")
    await mc_command(f"/gamemode {state} {player}")
    await ctx.send(f"{player} is now in {state} indefinitely.")
    lprint(f"Set {player} to: {state}")

@bot.command(aliases=['timedgamemode', 'timedgm', 'tgm'])
async def player_timed_gamemode(ctx, player, state, duration=None, *reason):
    try: 
        duration = int(duration)
    except: 
        await ctx.send("You buffoon, I need a number to set the duration!")
        return

    reason = format_args(reason)
    await mc_command(f"/say {player} set to {state} for {duration}s | Reason: {reason}.")
    await ctx.send(f"{player} set to {state} for {duration}s, then will revert to survival.")
    await mc_command(f"/gamemode {state} {player}")
    time.sleep(duration)
    await mc_command(f"/gamemode survival {player}")
    await ctx.send(f"{player} is back to survival.")
    lprint(f"Set gamemode: {player} for {duration}")


# ========== World weather, time, etc
@bot.command(aliases=['weather'])
async def server_weather(ctx, state, duration=0):
    await mc_command(f'/weather {state} {duration*60}')
    if duration: 
        await ctx.send(f"I see some {state} in the near future.")
    else: await ctx.send(f"Forecast entails {state}.")
    lprint(f"Weather set to: {state} for {duration}")

# ========== Server Start, stop, status, etc
@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    embed = discord.Embed(title='Help')
    for i in get_csv('command_info.csv'):
        embed.add_field(name=i[0], value=f"`{i[1]}`\n{', '.join(i[2:])}", inline=False)
    await ctx.send(embed=embed)
    lprint("Fetching help page.")

@bot.command(aliases=['status', 'serverstatus'])
async def server_status(ctx):
    if 'java' in (p.name() for p in psutil.process_iter()):
        await ctx.send("Server is __**ACTIVE**__.\nYou can use `?stop` to halt server.")
    else: await ctx.send("Server is __**INACTIVE**__.\nYou can use `?start` or `?restart` to activate server.")
    lprint("Fetching server status.")

@bot.command(aliases=['start', 'activate'])
async def server_start(ctx):
    if mc_funcs.start_server():
        await ctx.send("Starting server...\nPlease wait 5s for status...")
    else:
        await ctx.send("Error starting server, contact administrator.")
    time.sleep(5)
    await ctx.invoke(bot.get_command('status'))
    lprint("Starting server.")


@bot.command(aliases=['stop', 'deactivate', 'halt'])
async def server_stop(ctx):
    await mc_command('/say WARNING | Server will be halted in 15s')
    await ctx.send("Server will save world and be halted in 15s.")
    time.sleep(15)
    await mc_command('/save-all')
    time.sleep(3)
    await mc_command('/stop')
    await ctx.send("World Saved. Server __**HALTED**__")
    lprint("Stopping server.")

@bot.command(aliases=['restart', 'reboot'])
async def server_restart(ctx):
    await ctx.send("Will save and halt server (if not already) and restart.")
    await ctx.invoke(bot.get_command('stop'))
    await ctx.invoke(bot.get_command('start'))
    lprint("Restarting server.")


bot.run(TOKEN)

