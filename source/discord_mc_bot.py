import discord, asyncio, os, sys, psutil, time, json, csv, datetime, server_functions
from discord.ext import commands, tasks
from server_functions import lprint

bot_token_file = '/home/slime/mc_bot_token.txt'
# Exits script if no token.
with open(bot_token_file, 'r') as file:
    TOKEN = file.readline()
if not TOKEN: print("Token Error."), exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')

autosave = False

# Sends command to tmux window running server.
def mc_command(command):
    os.system(f'tmux send-keys -t mcserver:1.0 "{command}" ENTER')

def get_server_status():
    return 'java' in (p.name() for p in psutil.process_iter())

def format_args(args):
    if args:
        return ' '.join(args)
    else: return "No reason given"

# Gets data from json files in same local.
def get_json(json_file):
    os.chdir(server_functions.server_functions_path)
    with open(server_functions.server_path + '/' + json_file) as file:
        return [i for i in json.load(file)]

def get_csv(csv_file):
    os.chdir(server_functions.server_functions_path)
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
    mc_command(f"/{args}")
    lprint(ctx, "Sent command: " + args)

@bot.command(aliases=['save', 'sa'])
async def server_save(ctx):
    mc_command('/save-all')
    await ctx.send("I saved the world!")
    await ctx.send("**NOTE:** This is not the same as making a backup using `?backup`.")
    lprint(ctx, "Saved world.")

@bot.command(aliases=['say', 's'])
async def server_say(ctx, *msg):
    msg = format_args(msg)
    mc_command('/say ' + msg)
    await ctx.send("Message circulated to all active players!")
    lprint(ctx, "Server said: {msg}")

@bot.command(aliases=['tell', 'msg', 'whisper', 't'])
async def server_tell(ctx, player, *msg):
    msg = format_args(msg)
    mc_command(f"/tell {player} {msg}")
    await ctx.send("Communiqué transmitted to: `{player}`.")
    lprint(ctx, f"Messaged {player} : {msg}")

@bot.command(aliases=['list', 'users', 'players'])
async def list_players(ctx):
    mc_command("/list")
    time.sleep(1)
    
    log_data = server_functions.get_output(server_functions.server_log_file, match='players online')
    if not log_data:
        await ctx.send("**Error:** Trouble fetching player list.")
        return

    log_data = log_data.split(':')
    text = log_data[-2]
    player_data = log_data[-1]
    # If there's no players connected at the moment.
    if player_data == ' \n':
        await ctx.send(text)
    else:
        # Outputs player names in special discord format.
        players = [f"`{i.strip()}`" for i in (log_data[-1]).split(',')]
        await ctx.send(text + ':\n' + ''.join(players))


# ========== Permissions: Ban, Kick, Whitelist, OP, etc
@bot.command(aliases=['kick', 'k'])
async def player_kick(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f'/say WARNING | {player} will be ejected from server in 5s | {reason}.')
    time.sleep(5)
    mc_command(f"/kick {player}")
    await ctx.send(f"`{player}` is outta here!")
    lprint(ctx, f"Kicked {player}")

@bot.command(aliases=['ban', 'b'])
async def player_ban(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | Banishing {player} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"/kick {player}")
    mc_command(f"/ban {player} {reason}")
    await ctx.send(f"Dropkicked and exiled: `{player}`.")
    lprint(ctx, f"Banned {player} : {reason}")

@bot.command(aliases=['pardon', 'unban', 'p'])
async def player_pardon(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | {player} has been vindicated! | {reason}.")
    mc_command(f"/pardon {player}")
    await ctx.send(f"Cleansed `{player}`.")
    lprint(ctx, f"Pardoned {player} : {reason}")

@bot.command(aliases=['banlist', 'bl', 'blist'])
async def ban_list(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in get_json('banned-players.json')]: 
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)
    lprint(ctx, f"Fetching banned list.")

@bot.command(aliases=['oplist', 'ol', 'ops'])
async def op_list(ctx):
    op_players = [f"`{i['name']}`" for i in get_json('ops.json')]
    await ctx.send('\n'.join(op_players))
    lprint(ctx, f"Fetching server operators list.")

@bot.command(aliases=['opadd'])
async def op_add(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | {player} has become a God! | {reason}")
    mc_command(f"/op {player}")
    await ctx.send(f"`{player}` too op now. ||Please nerf soon rito!||")
    lprint(ctx, f"New server op: {player}")

@bot.command(aliases=['opremove'])
async def op_remove(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | {player} fell from grace! | {reason}")
    mc_command(f"/deop {player}")
    await ctx.send(f"`{player}` stripped of Godhood!")
    lprint(ctx, f"Removed server op: {player}")

@bot.command(aliases=['top', 'timedop'])
async def timed_op(ctx, player, time_limit=1):
    await ctx.send(f"Granting `{player}` OP status for {time_limit}m!")
    mc_command(f"/say INFO | {player} granted God status for {time_limit}m!")
    mc_command(f"/op {player}")
    lprint(ctx, f"OP {player} for {time_limit}.")
    time.sleep(time_limit*60)
    await ctx.send(f"Removed `{player}` OP status!")
    mc_command(f"/say INFO | {player} is back to being a mortal.")
    mc_command(f"/deop {player}")
    lprint(ctx, f"Remove OP {player}")


# ========== Player: gamemode, kill, tp, etc
@bot.command(aliases=['kill', 'assassinate'])
async def player_kill(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | {player} will be EXTERMINATED | {reason}.")
    mc_command(f'/kill {player}')
    await ctx.send(f"`{player}` assassinated!")
    lprint(ctx, f"Killed: {player}")

@bot.command(aliases=['delaykill', 'delayassassinate', 'dkill', 'dk'])
async def player_delay_kill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    mc_command(f"/say WARNING | {player} will self-destruct in {delay}s | {reason}.")
    time.sleep(delay)
    mc_command(f'/kill {player}')
    await ctx.send(f"`{player}` soul has been freed.")
    lprint(ctx, f"Delay killed: {player}")

@bot.command(aliases=['tp', 'teleport'])
async def player_teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    mc_command(f"/say INFO | Flinging {player} towards {target} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"/tp {player} {target}")
    await ctx.send(f"`{player}` and {target} touchin real close now.")
    lprint(ctx, f"Teleported {player} to {target}")

@bot.command(aliases=['gamemode', 'gm'])
async def player_gamemode(ctx, player, state, *reason):
    reason = format_args(reason)
    mc_command(f"/say {player} now in {state} | {reason}.")
    mc_command(f"/gamemode {state} {player}")
    await ctx.send(f"`{player}` is now in `{state}` indefinitely.")
    lprint(ctx, f"Set {player} to: {state}")

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
    lprint(ctx, f"Set gamemode: {player} for {duration}")


# ========== World weather, time, etc
@bot.command(aliases=['weather'])
async def world_weather(ctx, state, duration=0):
    mc_command(f'/weather {state} {duration*60}')
    if duration: 
        await ctx.send(f"I see some `{state}` in the near future.")
    else: await ctx.send(f"Forecast entails `{state}`.")
    lprint(ctx, f"Weather set to: {state} for {duration}")

@bot.command(aliases=['settime', 'time'])
async def world_time(ctx, set_time=None):
    if set_time:
        mc_command(f"/time set {set_time}")
        await ctx.send("Time updated!")
    else: await ctx.send("Need time input, like: `12`, `day`")


# ========== Server Start, status, backup, update, etc
@bot.command(aliases=['motd', 'servermessage'])
async def server_motd(ctx, *message):
    if message:
        message = format_args(message)
        server_functions.edit_properties('motd', message)
        await ctx.send("Message of the day updates!")
    else: await ctx.send(server_functions.edit_properties('motd')[1])

@bot.command(aliases=['status', 'serverstatus'])
async def server_status(ctx):
    if get_server_status():
        await ctx.send("Server is now __**ACTIVE**__.")
    else: await ctx.send("Server is __**INACTIVE**__.")
    lprint(ctx, "Fetching server status.")

@bot.command(aliases=['start', 'activate'])
async def server_start(ctx):
    if server_functions.start_server():
        await ctx.send("***Booting Server...***")
    else: await ctx.send("**Error** starting server, contact administrator!")
    time.sleep(5)
    await ctx.send("***Fetching server status...***")
    await ctx.invoke(bot.get_command('status'))
    lprint(ctx, "Starting server.")

@bot.command(aliases=['stop', 'deactivate', 'halt'])
async def server_stop(ctx):
    mc_command('/say WARNING | Server will halt in 15s!')
    await ctx.send("***Halting in 15s...***")
    time.sleep(10)
    mc_command('/say WARNING | 5s left!')
    time.sleep(5)
    mc_command('/stop')
    await ctx.send("World Saved. Server __**HALTED**__")
    lprint(ctx, "Stopping server.")

@bot.command(aliases=['restart', 'reboot'])
async def server_restart(ctx):
    lprint(ctx, "Restarting server.")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    time.sleep(5)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['saves', 'worlds', 'backups', 'showsaves', 'showbackups', 'sb'])
async def fetch_worlds(ctx, amount=5):
    embed = discord.Embed(title='World Backups')
    worlds = server_functions.fetch_worlds(amount)
    for save in worlds:
        embed.add_field(name=worlds.index(save), value=f"`{save}`", inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?restore <index>` to restore world save.")
    await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
    lprint(ctx, f"Fetching {amount} most recent world saves.")

@bot.command(aliases=['backup', 'clone', 'saveworld'])
async def backup_world(ctx, *name):
    if not name:
        await ctx.send("Hey! I need a name or keywords to make a backup!")
        return

    name = format_args(name)
    mc_command(f"/say INFO | Standby, world is currently being archived. Codename: {name}")
    await ctx.send("***Saving current world...***")
    mc_command(f"/save-all")
    time.sleep(5)
    backup = server_functions.backup_world(name)
    if backup:
        await ctx.send(f"Cloned and archived your world to:\n`{backup}`.")
    else: await ctx.send("**Error** saving the world! || it's doomed!||")
    await ctx.invoke(bot.get_command('saves'))
    lprint(ctx, "New backup: " + backup)

@bot.command(aliases=['restore', 'jumpto', 'saverestore', 'restoresave', 'worldrestore', 'restoreworld'])
async def restore_world(ctx, index=None):
    try: index = int(index)
    except:
        await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
        return

    restore = server_functions.get_world_from_index(index)
    lprint(ctx, "Restoring to: " + restore)
    await ctx.send(f"***Restoring...*** `{restore}`")
    mc_command(f"/say WARNING | Initiating jump to save point in 5s! | {restore}")
    time.sleep(5)

    # Stops server if running
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_world(restore)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['deletesave', 'rmsave', 'delete', 'deleteworld', 'killworld', 'ksave'])
async def delete_world(ctx, index):
    try: index = int(index)
    except:
        await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
        return

    to_delete = server_functions.get_world_from_index(index)
    server_functions.delete_world(to_delete)
    await ctx.send(f"World as been incinerated!")
    await ctx.invoke(bot.get_command('saves'))
    lprint(ctx, "Deleted: " + to_delete)

@bot.command(aliases=['newworld', 'startover', 'rebirth'])
async def new_world(ctx):
    mc_command("/say WARNING | Commencing project Rebirth in T-5s!")
    await ctx.send(":fire:**INCINERATED:**fire:")
    await ctx.send("**NOTE:** Next startup will take longer, to generate new world. Also, server settings will be preserved, this does not include data like player's gamemode status, inventory, etc.")
    if get_server_status(): await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_world(reset=True)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

# Edit server properties.
@bot.command(aliases=['properties', 'property'])
async def server_properties(ctx, target_property, *value):
    if not value:
        value = ''
    else: value = ' '.join(value)
    await ctx.send(server_functions.edit_properties(target_property, value)[1])

@bot.command(aliases=['update', 'serverupdate'])
async def server_update(ctx):
    lprint(ctx, "**Updating** `server.jar`...")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    time.sleep(5)
    server = server_functions.download_new_server()
    if server:
        await ctx.send(f"Downloaded latest version: `{server}`!")
        time.sleep(3)
        await ctx.invoke(bot.get_command('start'))
    else: await ctx.send("**Error:** Updating server. Suggest restoring from a backup.")

@bot.command(aliases=['version', 'ver'])
async def server_version(ctx):
    await ctx.send(f"`{server_functions.get_minecraft_version()}`")
    lprint(ctx, "Get Minecraft server version.")

@bot.command(aliases=['serverlist', 'servers', 'serversaves', 'serverbackups'])
async def server_list(ctx, amount=5):
    embed = discord.Embed(title='Server Backups')
    servers = server_functions.fetch_servers(amount)
    for save in servers:
        embed.add_field(name=servers.index(save), value=f"`{save}`", inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?serverrestore <index>` to restore server.")
    await ctx.send("**WARNING:** Restore will overwrite current server. Make a backup using `?serverbackup <codename>`.")
    lprint(ctx, f"Fetched latest {amount} world saves.")

@bot.command(aliases=['serverbackup', 'backupserver', 'saveserver', 'serversave'])
async def server_backup(ctx, *name):
    if not name:
        await ctx.send("Hey! I need a name or keywords to make a backup!")
        return

    name = format_args(name)
    await ctx.send("***Backing Up...***")

    mc_command(f"/save-all")
    time.sleep(5)
    backup = server_functions.backup_server(name)

    if backup:
        await ctx.send(f"New backup:\n`{backup}`.")
    else: await ctx.send("**Error** saving server!")

    await ctx.invoke(bot.get_command('servers'))
    lprint(ctx, "New backup: " + backup)

@bot.command(aliases=['serverrestore', 'restoreserver'])
async def server_restore(ctx, index=None):
    try: index = int(index)
    except:
        await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
        return

    restore = server_functions.get_server_from_index(index)
    lprint(ctx, "Restoring to: " + restore)
    await ctx.send(f"***Restoring...*** `{restore}`")
    mc_command(f"/say WARNING | Initiating jump to save point in 5s! | {restore}")
    time.sleep(5)

    # Stops server if running
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))

    if server_functions.restore_server(restore):
        await ctx.send("Server **Restored!**")
    else: await ctx.send("**Error:** Could not restore server!")

    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['deleteserver', 'rmserver', 'serverdelete', 'rmserversave', 'rmserverbackup'])
async def server_delete(ctx, index):
    try: index = int(index)
    except:
        await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
        return

    to_delete = server_functions.get_server_from_index(index)
    server_functions.delete_server(to_delete)
    await ctx.send(f"Server backup deleted!")
    await ctx.invoke(bot.get_command('servers'))
    lprint(ctx, "Deleted: " + to_delete)

@bot.command(aliases=['serverreset', 'resetserver'])
async def server_reset(ctx):
    mc_command("/say WARNING | Resetting server in 5s!")
    await ctx.send("**Resetting Server...**")
    await ctx.send("**NOTE:** Next startup will take longer, to setup server and generate new world. Also `server.properties` file will reset!")

    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_server(reset=True)

    time.sleep(5)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['log', 'getlog', 'showlog'])
async def server_log(ctx, lines=10):
    log_data = server_functions.get_output(server_functions.server_log_file, lines)
    await ctx.send(f"`{log_data}`")


# Restarts this bot script.
@bot.command(aliases=['restartbot', 'rbot', 'rebootbot'])
async def bot_restart(ctx):
    os.chdir(server_functions.server_functions_path)
    await ctx.send("***Rebooting Bot...***")
    os.execl(sys.executable, sys.executable, *sys.argv)
    lprint(ctx, "Restarting bot.")

@bot.remove_command("help")
@bot.command(aliases=['help', 'h'])
async def help_page(ctx):
    current_command, embed_page, contents = 0, 1, []
    pages, current_page, page_limit = 3, 1, 15
    def new_embed(page):
        return discord.Embed(title=f'Help Page {page}/{pages}')

    embed = new_embed(embed_page)
    for command in get_csv('command_info.csv'):
        if not command:  continue

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
