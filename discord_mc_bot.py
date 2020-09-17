import discord, asyncio, os, sys, psutil, time, json, csv, datetime, mc_funcs
from discord.ext import commands, tasks
from mc_funcs import lprint, server_path, file_path

# Exits script if no token.
with open('/home/slime/mc_bot_token.txt', 'r') as file: TOKEN = file.readline()
if not TOKEN: print("Token Error."), exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')

# Sends command to tmux window running server.
def mc_command(command): os.system(f'tmux send-keys -t mcserver:1.0 "{command}" ENTER')

def get_server_status(): return 'java' in (p.name() for p in psutil.process_iter())

def format_args(args):
    if args: return ' '.join(args)
    else: return "No reason given"

# Gets data from json files in same local.
def get_json(json_file):
    os.chdir(file_path)
    with open(server_path + '/' + json_file) as file: 
        return [i for i in json.load(file)]

def get_csv(csv_file):
    os.chdir(file_path)
    with open(csv_file) as file: 
        return [i for i in csv.reader(file, delimiter=',', skipinitialspace=True)]

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    lprint("Bot PRIMED.")

# ========== Common Server Functions.
@bot.command(aliases=['save', 'sa'])
async def server_save(ctx):
    mc_command('/save-all')
    await ctx.send("I saved the world!")
    await ctx.send("**NOTE:** This is not the same as backing up using `?backup`.")
    lprint("Saved world.")

@bot.command(aliases=['say', 's'])
async def server_say(ctx, *msg):
    msg = format_args(msg)
    mc_command('/say ' + msg)
    await ctx.send("Message circulated to all active players!")
    lprint("Server said: {msg}")

@bot.command(aliases=['tell', 'msg', 'whisper', 't'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    mc_command(f"/tell {player} {msg}")
    await ctx.send("Communiqué transmitted to: `{player}`.")
    lprint(f"Messaged {player} : {msg}")


# ========== Permissions: Ban, Kick, Whitelist, OP, etc
@bot.command(aliases=['kick', 'k'])
async def server_kick(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f'/say WARNING | {player} will be ejected from server in 5s | {reason}.')
    time.sleep(5)
    mc_command(f"/kick {player}")
    await ctx.send(f"`{player}` is outta here!")
    lprint(f"Kicked {player}")

@bot.command(aliases=['ban', 'b'])
async def server_ban(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | Banishing {player} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"/kick {player}")
    mc_command(f"/ban {player} {reason}")
    await ctx.send(f"Dropkicked and exiled: `{player}`.")
    lprint(f"Banned {player} : {reason}")

@bot.command(aliases=['pardon', 'unban', 'p'])
async def server_pardon(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | {player} has been vindicated! | {reason}.")
    mc_command(f"/pardon {player}")
    await ctx.send(f"Cleansed `{player}`.")
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
    mc_command(f"/say INFO | {player} has become a God! | {reason}")
    mc_command(f"/op {player}")
    await ctx.send(f"`{player}` too op now. ||Please nerf soon rito!||")
    lprint(f"New server op: {player}")

@bot.command(aliases=['opremove'])
async def server_op_remove(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | {player} fell from grace! | {reason}")
    mc_command(f"/deop {player}")
    await ctx.send(f"`{player}` stripped of Godhood!")
    lprint(f"Removed server op: {player}")


# ========== Player: gamemode, kill, tp, etc
@bot.command(aliases=['kill', 'assassinate'])
async def player_kill(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | {player} will be EXTERMINATED | {reason}.")
    mc_command(f'/kill {player}')
    await ctx.send(f"`{player}` assassinated!")
    lprint(f"Killed: {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill', 'dk'])
async def player_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | {player} will self-destruct in {delay}s | {reason}.")
    time.sleep(delay)
    mc_command(f'/kill {player}')
    await ctx.send(f"`{player}` soul has been freed.")
    lprint(f"Delay killed: {player}")

@bot.command(aliases=['tp', 'teleport'])
async def player_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | Flinging {player} towards {target} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"/tp {player} {target}")
    await ctx.send(f"`{player}` and {target} touchin real close now.")
    lprint(f"Teleported {player} to {target}")

@bot.command(aliases=['gamemode', 'gm'])
async def player_gamemode(ctx, player, state, *reason):
    reason = format_args(reason)
    mc_command(f"/say {player} now in {state} | {reason}.")
    mc_command(f"/gamemode {state} {player}")
    await ctx.send(f"`{player}` is now in `{state}` indefinitely.")
    lprint(f"Set {player} to: {state}")

@bot.command(aliases=['timedgamemode', 'timedgm', 'tgm'])
async def player_timed_gamemode(ctx, player, state, duration=None, *reason):
    try: duration = int(duration)
    except: 
        await ctx.send("You buffoon, I need a number to set the duration!")
        return

    reason = format_args(reason)
    mc_command(f"/say {player} set to {state} for {duration}s | {reason}.")
    await ctx.send(f"`{player}` set to `{state}` for {duration}s, then will revert to survival.")
    mc_command(f"/gamemode {state} {player}")
    time.sleep(duration)
    mc_command(f"/gamemode survival {player}")
    await ctx.send(f"`{player}` is back to survival.")
    lprint(f"Set gamemode: {player} for {duration}")


# ========== World weather, time, etc
@bot.command(aliases=['weather'])
async def server_weather(ctx, state, duration=0):
    mc_command(f'/weather {state} {duration*60}')
    if duration: 
        await ctx.send(f"I see some `{state}` in the near future.")
    else: await ctx.send(f"Forecast entails `{state}`.")
    lprint(f"Weather set to: {state} for {duration}")

# ========== Server Start, stop, status, backup, restore, etc
@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    x, embed_page, contents = 0, 1, []
    pages, current_page, page_limit = 2, 1, 15
    def new_embed(page): return discord.Embed(title=f'Help Page {page}')

    embed = new_embed(embed_page)
    for i in get_csv('command_info.csv'):
        if not i: continue
        embed.add_field(name=i[0], value=f"`{i[1]}`\n{', '.join(i[2:])}", inline=False)
        x += 1
        if not x % page_limit:
            embed_page += 1
            contents.append(embed)
            embed = new_embed(embed_page)
    contents.append(embed)


    # getting the message object for editing and reacting
    message = await ctx.send(embed=contents[0])
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    # This makes sure nobody except the command sender can interact with the "menu"
    def check(reaction, user): return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

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

@bot.command(aliases=['status', 'serverstatus'])
async def server_status(ctx):
    if get_server_status():
        await ctx.send("Server is now __**ACTIVE**__.")
    else: await ctx.send("Server is __**INACTIVE**__.")
    lprint("Fetching server status.")

@bot.command(aliases=['start', 'activate'])
async def server_start(ctx):
    if mc_funcs.start_server():
        await ctx.send("***Starting server...***")
    else: await ctx.send("**Error** starting server, contact administrator!")
    time.sleep(5)
    await ctx.send("***Fetching server status...***")
    await ctx.invoke(bot.get_command('status'))
    lprint("Starting server.")


@bot.command(aliases=['stop', 'deactivate', 'halt'])
async def server_stop(ctx):
    mc_command('/say WARNING | Server will halt in 15s!')
    await ctx.send("***Halting in 15s...***")
    time.sleep(10)
    mc_command('/say WARNING | 5s left!')
    time.sleep(5)
    mc_command('/stop')
    await ctx.send("World Saved. Server __**HALTED**__")
    lprint("Stopping server.")

@bot.command(aliases=['restart', 'reboot'])
async def server_restart(ctx):
    lprint("Restarting server.")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    time.sleep(5)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['saves', 'worlds', 'backups', 'showsaves', 'showbackups'])
async def fetch_worlds(ctx, amount=5):
    embed = discord.Embed(title='World Saves')
    for index, save in mc_funcs.fetch_worlds(5): 
        embed.add_field(name=index, value=f"`{save}`", inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?restore <index>` to restore world save.")
    await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
    lprint(f"Fetching latest {amount} world saves.")

@bot.command(aliases=['backup', 'clone'])
async def backup_world(ctx, *name):
    if not name:
        await ctx.send("Hey! I need a name or keywords to make a backup!")
        return

    name = format_args(name)

    mc_command(f"/say INFO | Standby, world is currently being archived. Codename: {name}")
    await ctx.send("***Saving current world...***")
    mc_command(f"/save-all")
    time.sleep(5)
    backup = mc_funcs.backup_world(name)
    if backup:
        await ctx.send(f"Cloned and archived your world to:\n`{backup}`.")
    else: await ctx.send("**Error** saving the world! || it's doomed!||")
    await ctx.invoke(bot.get_command('saves'))
    lprint("New backup: " + backup)


@bot.command(aliases=['restore', 'jumpto'])
async def restore_world(ctx, index=None):
    try: index = int(index)
    except:
        await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
        return

    restore = mc_funcs.get_world_from_index(index)
    lprint("Restoring to: " + restore)
    await ctx.send(f"***Restoring...*** `{restore}`")
    mc_command(f"/say WARNING | Initiating jump to save point in 5s! | {restore}")
    time.sleep(5)

    # Stops server if running
    if get_server_status(): await ctx.invoke(bot.get_command('stop'))
    mc_funcs.restore_world(restore)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['deletesave', 'rmsave', 'delete', 'killsave', 'killworld', 'ksave'])
async def delete_world(ctx, index):
    try: index = int(index)
    except:
        await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
        return

    to_delete = mc_funcs.get_world_from_index(index)
    mc_funcs.delete_world(to_delete)
    await ctx.send(f"World as been incinerated!")
    await ctx.invoke(bot.get_command('saves'))
    lprint("Deleted: " + to_delete)

@bot.command(aliases=['newworld', 'startover', 'rebirth'])
async def new_world(ctx):
    mc_command("/say WARNING | Commencing project Rebirth in T-5s!")
    await ctx.send(":fire:**INCINERATED:**fire:")
    await ctx.send("**NOTE:** Next startup will take longer, to generate new world. Also, server settings will be preserved, this does not include data like player's gamemode status, inventory, etc.")
    if get_server_status(): await ctx.invoke(bot.get_command('stop'))
    mc_funcs.restore_world(reset=True)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

# Edit server properties.
@bot.command(aliases=['properties', 'property'])
async def server_properties(ctx, target_property, value=''): await ctx.send(mc_funcs.edit_properties(target_property, value))

# Restarts this bot script.
@bot.command(aliases=['restartbot', 'rbot', 'rebootbot'])
async def bot_restart(ctx):
    os.chdir(file_path)
    os.execl(sys.executable, sys.executable, *sys.argv)


bot.run(TOKEN)
