import discord, asyncio, os, time, json, csv, psutil
from discord.ext import commands, tasks
from datetime import datetime
import start_server

mc_server_dir = '/mnt/c/Users/DT/Desktop/MC/server'

with open('/home/slime/mc_bot_token.txt', 'r') as file: TOKEN = file.readline()

if not TOKEN:
    print("Token Error.")
    exit()

bot = commands.Bot(command_prefix='?')

def sprint(msg): print(f'{datetime.today()} | {msg}')

async def mc_command(command): 
    os.system(f'tmux send-keys -t mcserver:1.0 "{command}" ENTER')

def format_args(args):
    if not args: return "No reason given"
    else: return ' '.join(args)

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
    sprint("Bot ready.")

@bot.command(aliases=['save', 'sa'])
async def server_save(ctx):
    await mc_command('/save-all')
    await ctx.send("World saved.")

@bot.command(aliases=['say', 's'])
async def server_say(ctx, *msg):
    msg = format_args(msg)
    await mc_command('/say ' + msg)
    await ctx.send("Message sent.")

@bot.command(aliases=['tell', 'msg', 'whisper', 't'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    await mc_command(f"/tell {player} {msg}")
    await ctx.send("Sent message to {player}.")


# ========== Ban, Kick, Whitelist, OP, etc
@bot.command(aliases=['kick', 'k'])
async def server_kick(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f'/say WARNING | {player} will be kicked in 5s for: {reason}.')
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await ctx.send(f"Kicked {player}.")

@bot.command(aliases=['ban', 'b'])
async def server_ban(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | {player} will be banned in 5s for: {reason}.")
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await mc_command(f"/ban {player} {reason}")
    await ctx.send(f"Banned {player}.")

@bot.command(aliases=['pardon', 'unban', 'p'])
async def server_pardon(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} pardoned because: {reason}.")
    await mc_command(f"/pardon {player}")
    await ctx.send(f"Pardoned {player} for: {reason}.")

@bot.command(aliases=['banlist', 'bl', 'blist'])
async def server_ban_list(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in get_json('banned-players.json')]: 
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)

@bot.command(aliases=['oplist', 'ol', 'ops'])
async def server_op_list(ctx):
    op_players = [f"`{i['name']}`" for i in get_json('ops.json')]
    await ctx.send('\n'.join(op_players))

@bot.command(aliases=['opadd'])
async def server_op_add(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} is now a server operator because: {reason}")
    await mc_command(f"/op {player}")
    await ctx.send(f"{player} is now a server operator.")

@bot.command(aliases=['opremove'])
async def server_op_remove(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | {player} is no longer a server operator because: {reason}")
    await mc_command(f"/deop {player}")
    await ctx.send(f"{player} is no longer a server operator.")


# ========== Player kill, tp, etc
@bot.command(aliases=['kill', 'assassinate'])
async def server_kill(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | Killing {player} because: {reason}.")
    await mc_command(f'/kill {player}')
    await ctx.send("Killed {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill', 'dk'])
async def server_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    await mc_command(f"/say WARNING | Killing {player} in {delay}s because: {reason}.")
    time.sleep(delay)
    await mc_command(f'/kill {player}')
    await ctx.send(f"Killed {player}.")

@bot.command(aliases=['tp', 'teleport'])
async def server_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    await mc_command(f"/say INFO | Teleporting {player} to {target} in 5s because: {reason}")
    time.sleep(5)
    await mc_command(f"/tp {player} {target}")
    await ctx.send(f"Teleported {player}.")


# ========== World weather, etc
@bot.command(aliases=['weather'])
async def server_weather(ctx, state, duration=0):
    await mc_command(f'/weather {state} {duration*60}')
    await ctx.send("Weather set for {state} for {duration*60}.")


# ========== Server Start, stop, status, etc
@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    embed = discord.Embed(title='Help')
    for i in get_csv('command_info.csv'):
        embed.add_field(name=i[0], value=f"`{i[1]}`\n{', '.join(i[2:])}", inline=False)
    await ctx.send(embed=embed)

@bot.command(aliases=['status', 'serverstatus'])
async def server_status(ctx):
    if 'java' in (p.name() for p in psutil.process_iter()):
        await ctx.send("Server is __**ACTIVE**__.\nYou can use `?stop` to halt server.")
    else: await ctx.send("Server is __**INACTIVE**__.\nYou can use `?start` or `?restart` to activate server.")

@bot.command(aliases=['start', 'activate'])
async def server_start(ctx):
    if start_server.start_server():
        await ctx.send("Starting server...\nPlease wait 5s for status...")
    else:
        await ctx.send("Error starting server, contact administrator.")
    time.sleep(5)
    await ctx.invoke(bot.get_command('status'))


@bot.command(aliases=['stop', 'deactivate', 'halt'])
async def server_stop(ctx):
    await mc_command('/say WARNING | Server will be halted in 15s')
    await ctx.send("Server will save world and be halted in 15s.")
    time.sleep(15)
    await mc_command('/save-all')
    time.sleep(3)
    await mc_command('/stop')
    await ctx.send("World Saved. Server __**HALTED**__")

@bot.command(aliases=['restart', 'reboot'])
async def server_restart(ctx):
    await ctx.send("Will save and halt server (if not already) and restart.")
    await ctx.invoke(bot.get_command('stop'))
    await ctx.invoke(bot.get_command('start'))


bot.run(TOKEN)

