import discord, asyncio, os, time, json, csv
from discord.ext import commands, tasks
from datetime import datetime

mc_server_dir = '/mnt/c/Users/DT/Desktop/MC/server'
with open('/home/slime/mc_bot_token.txt', 'r') as file:
    TOKEN = file.readline()

if not TOKEN:
    print("Token Error.")
    exit()

bot = commands.Bot(command_prefix='?')

def sprint(msg): print(f'{datetime.today()} | {msg}')

async def mc_command(command): 
    os.system(f'tmux send-keys -t mcserver "{command}" ENTER')

def format_args(args):
    if not args: return "No reason given"
    else: return ' '.join(args)

def get_json(json_file):
    with open(mc_server_dir + '/' + json_file) as file: 
        return [i for i in json.load(file)]

def get_csv(csv_file):
    with open(csv_file) as file: 
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    sprint("Bot ready.")

@bot.command(aliases=['save'])
async def server_save(ctx):
    await mc_command('/save-all')
    await ctx.send("World saved.")

@bot.command(aliases=['say'])
async def server_say(ctx, *msg):
    msg = format_args(msg)
    await mc_command('/say ' + msg)
    await ctx.send("Message sent.")

@bot.command(aliases=['tell', 'msg', 'whisper'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    await mc_command(f"/tell {player} {msg}")
    await ctx.send("Sent message to {player}.")

# ========== Ban, Kick, Whitelist, etc
@bot.command(aliases=['kick'])
async def server_kick(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f'/say {player} will be kicked in 5s for: {reason}.')
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await ctx.send(f"Kicked {player}.")

@bot.command(aliases=['ban'])
async def server_ban(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say {player} will be banned in 5s for: {reason}.")
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await mc_command(f"/ban {player} {reason}")
    await ctx.send(f"Banned {player}.")

@bot.command(aliases=['pardon', 'unban'])
async def server_pardon(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say {player} pardoned for: {reason}.")
    await mc_command(f"/pardon {player}")
    await ctx.send(f"Pardoned {player} for: {reason}.")

@bot.command(aliases=['banlist', 'blist'])
async def server_ban_list(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in get_json('banned-players.json')]: 
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)

# ========== Player op, kill, tp, etc
@bot.command(aliases=['oplist', 'showop', 'ops'])
async def server_op_list(ctx):
    op_players = [f"`{i['name']}`" for i in get_json('ops.json')]
    await ctx.send('\n'.join(op_players))

@bot.command(aliases=['kill', 'assassinate'])
async def server_kill(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say Killing {player} for: {reason}.")
    await mc_command(f'/kill {player}')
    await ctx.send("Killed {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill'])
async def server_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    await mc_command(f"/say Killing {player} in {delay}s for: {reason}.")
    time.sleep(delay)
    await mc_command(f'/kill {player}')
    await ctx.send(f"Killed {player}.")

@bot.command(aliases=['tp', 'teleport'])
async def server_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    await mc_command(f"/say Teleporting {player} to {target} in 5s for: {reason}")
    time.sleep(5)
    await mc_command(f"/tp {player} {target}")
    await ctx.send(f"Teleported {player}.")


# ========== World weather, etc
@bot.command(aliases=['weather'])
async def server_weather(ctx, state, duration=0):
    await mc_command(f'/weather {state} {duration*60}')
    await ctx.send("Weather set for {state} for {duration*60}.")


@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    embed = discord.Embed(title='Help')
    for i in get_csv('command_info.csv'):
        embed.add_field(name=i[0], value=f"`{i[1]}`\n{', '.join(i[2:])}", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)

