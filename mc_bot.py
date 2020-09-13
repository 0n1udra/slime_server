import discord, asyncio, os, time
from discord.ext import commands, tasks
from datetime import datetime

with open('/home/slime/mc_bot_token.txt', 'r') as file:
    TOKEN = file.readline()

if not TOKEN:
    print("Token Error.")
    exit()

bot = commands.Bot(command_prefix='?')

def sprint(msg):
    print(f'{datetime.today()} | {msg}')

async def mc_command(command):
    os.system(f'tmux send-keys -t mcserver "{command}" ENTER')

def format_args(args):
    if not args: return "No reason given."
    else: return ' '.join(args)

@bot.event
async def on_ready():
    await bot.wait_until_ready()

@bot.command(aliases=['say'])
async def server_say(ctx, *msg):
    await mc_command('/say ' + ' '.join(msg))
    await ctx.send("Message Sent!")
    sprint('Server said: ' + ' '.join(msg))

@bot.command(aliases=['save'])
async def server_save(ctx):
    await mc_command('/save-all')
    await ctx.send("World Saved!")
    sprint("World Saved.")


@bot.command(aliases=['kick'])
async def server_kick(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f'/say {player} will be kicked in 5s for: {reason}')
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await ctx.send(f"Kicked {player} for: {reason}")

    sprint(f"Kicked {player} for: {reason}")

@bot.command(aliases=['ban'])
async def server_ban(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say {player} will be banned in 5s for: {reason}")
    time.sleep(5)
    await mc_command(f"/kick {player}")
    await mc_command(f"/ban {player}")
    await ctx.send(f"Banned {player} for {reason}")

    sprint(f"Banned {player} for: {reason}")

@bot.command(aliases=['pardon', 'unban'])
async def server_pardon(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say {player} pardoned for: {reason}")
    await mc_command(f"/pardon {player}")
    await ctx.send(f"Pardoned {player} for: {reason}")

@bot.command(aliases=['tell', 'msg', 'whisper'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    await mc_command(f"/tell {player} {msg}")
    sprint(f"Messaged {player}: {msg}")

@bot.command(aliases=['kill', 'assassinate'])
async def server_kill(ctx, player, *reason):
    reason = format_args(reason)
    await mc_command(f"/say Killing {player} for: {reason}")
    await mc_command(f'/kill {player}')
    sprint(f"Killed {player} for: {reason}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill'])
async def server_delay_kill(ctx, player, time=5, *reason):
    reason = format_args(reason)
    await mc_command(f"/say Killing {player} in {time}s for: {reason}")
    sprint(f"Killing {player} in {time}s for: {reason}")
    time.sleep(time)
    await mc_command(f'/kill {player}')
    sprint(f"Killed {player}")


bot.run(TOKEN)

