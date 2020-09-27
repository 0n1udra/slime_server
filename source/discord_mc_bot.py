import discord, asyncio, os, sys, time, server_functions
from discord.ext import commands, tasks
from server_functions import lprint, use_rcon, format_args, mc_command, get_server_status

# Exits script if no token.
if os.path.isfile(server_functions.bot_token_file):
    with open(server_functions.bot_token_file, 'r') as file:
        TOKEN = file.readline()
else: print("Missing Token File:", server_functions.bot_token_file), exit()

# Make sure this doesn't conflict with other bots.
bot = commands.Bot(command_prefix='?')

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    lprint("Bot PRIMED.")


# ========== Common Server Functions.
@bot.command(aliases=['/' ])
async def server_command(ctx, *args):
    args = format_args(args)
    mc_command(f"{args}")
    lprint(ctx, "Sent command: " + args)
    time.sleep(1)
    await ctx.invoke(bot.get_command('serverlog'), lines=2)

@bot.command()
async def saveall(ctx):
    mc_command('save-all')
    await ctx.send("I saved the world!")
    await ctx.send("**NOTE:** This is not the same as making a backup using `?backup`.")
    lprint(ctx, "Saved world.")

@bot.command()
async def say(ctx, *msg):
    msg = format_args(msg, return_empty=True)
    mc_command('say ' + msg)
    if not msg:
        await ctx.send("Usage exmaple: `?s Hello everyone!`")
    else: await ctx.send("Message circulated to all active players!")
    lprint(ctx, "Server said: {msg}")

@bot.command()
async def tell(ctx, player, *msg):
    msg = format_args(msg)
    mc_command(f"tell {player} {msg}")
    await ctx.send("Communiqué transmitted to: `{player}`.")
    lprint(ctx, f"Messaged {player} : {msg}")

@bot.command()
async def players(ctx):
    response = mc_command("list")

    if use_rcon: log_data = response
    else:
        time.sleep(1)
        log_data = server_functions.get_output('players online')

    if not log_data:
        await ctx.send("**Error:** Trouble fetching player list.")
        return

    log_data = log_data.split(':')
    text = log_data[-2]
    player_names = log_data[-1]
    # If there's no players connected at the moment. Even if no players online, player_names will still contain some escape characters and other chars.
    if len(player_names.strip()) < 5:
        await ctx.send(text)
    else:
        # Outputs player names in special discord format. If using RCON, need to clip off 4 trailing unreadable characters.
        players = [f"`{i.strip()[:-4]}`\n" if use_rcon else f"`{i.strip()}`\n" for i in (log_data[-1]).split(',')]
        await ctx.send(text + ':\n' + ''.join(players))
    lprint(ctx, "Fetched player list.")


# ========== Permissions: Ban, Kick, Whitelist, OP, etc
@bot.command()
async def kick(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f'say WARNING | {player} will be ejected from server in 5s | {reason}.')
    time.sleep(5)
    mc_command(f"kick {player}")
    await ctx.send(f"`{player}` is outta here!")
    lprint(ctx, f"Kicked {player}")

@bot.command()
async def ban(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | Banishing {player} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"kick {player}")
    mc_command(f"ban {player} {reason}")
    await ctx.send(f"Dropkicked and exiled: `{player}`.")
    lprint(ctx, f"Banned {player} : {reason}")

@bot.command(aliases=['unban'])
async def pardon(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} has been vindicated! | {reason}.")
    mc_command(f"pardon {player}")
    await ctx.send(f"Cleansed `{player}`.")
    lprint(ctx, f"Pardoned {player} : {reason}")

@bot.command()
async def banlist(ctx):
    embed = discord.Embed(title='Banned Players')
    for player in [i for i in server_functions.get_json('banned-players.json')]:
        embed.add_field(name=player['name'], value=player['reason'])
    await ctx.send(embed=embed)
    lprint(ctx, f"Fetched banned list.")

@bot.command()
async def oplist(ctx):
    op_players = [f"`{i['name']}`" for i in server_functions.get_json('ops.json')]
    await ctx.send('\n'.join(op_players))
    lprint(ctx, f"Fetched server operators list.")

@bot.command()
async def opadd(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} has become a God! | {reason}")
    mc_command(f"op {player}")
    await ctx.send(f"`{player}` too op now. ||Please nerf soon rito!||")
    lprint(ctx, f"New server op: {player}")

@bot.command()
async def opremove(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | {player} fell from grace! | {reason}")
    mc_command(f"deop {player}")
    await ctx.send(f"`{player}` stripped of Godhood!")
    lprint(ctx, f"Removed server op: {player}")

@bot.command(aliases=['timedop'])
async def optimed(ctx, player, time_limit=1):
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
@bot.command(aliases=['kill'])
async def player_kill(ctx, player, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | {player} will be EXTERMINATED! | {reason}.")
    mc_command(f'kill {player}')
    await ctx.send(f"`{player}` assassinated!")
    lprint(ctx, f"Killed: {player}")

@bot.command(aliases=['delaykill'])
async def delayedkill(ctx, player, delay=5, *reason):
    reason = format_args(reason)
    mc_command(f"say WARNING | {player} will self-destruct in {delay}s | {reason}.")
    time.sleep(delay)
    mc_command(f'kill {player}')
    await ctx.send(f"`{player}` soul has been freed.")
    lprint(ctx, f"Delay killed: {player}")

@bot.command(aliases=['tp'])
async def teleport(ctx, player, target, *reason):
    reason = format_args(reason)
    mc_command(f"say INFO | Flinging {player} towards {target} in 5s | {reason}.")
    time.sleep(5)
    mc_command(f"tp {player} {target}")
    await ctx.send(f"`{player}` and {target} touchin real close now.")
    lprint(ctx, f"Teleported {player} to {target}")

@bot.command()
async def gamemode(ctx, player, state, *reason):
    reason = format_args(reason)
    mc_command(f"say {player} now in {state} | {reason}.")
    mc_command(f"gamemode {state} {player}")
    await ctx.send(f"`{player}` is now in `{state}` indefinitely.")
    lprint(ctx, f"Set {player} to: {state}")

@bot.command(aliases=['timedgamemodde'])
async def gamemodetimed(ctx, player, state, duration=None, *reason):
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
@bot.command(aliases=['time'])
async def set_weather(ctx, state, duration=0):
    mc_command(f'weather {state} {duration*60}')
    if duration: 
        await ctx.send(f"I see some `{state}` in the near future.")
    else: await ctx.send(f"Forecast entails `{state}`.")
    lprint(ctx, f"Weather set to: {state} for {duration}")

@bot.command(aliases=['weather'])
async def set_time(ctx, set_time=None):
    if set_time:
        mc_command(f"time set {set_time}")
        await ctx.send("Time updated!")
    else: await ctx.send("Need time input, like: `12`, `day`")


# ========== Server Start, status, backup, update, etc
@bot.command(aliases=['info', 'stat', 'stats'])
async def status(ctx, show_players=True):
    stats = get_server_status()
    if stats:
        await ctx.send("Server is now __**ACTIVE**__.")
        await ctx.send(f"version: `{stats['version']}`")
        await ctx.send(f"motd: `{stats['motd']}`")
        if show_players: await ctx.invoke(bot.get_command('players'))
    else: await ctx.send("Server is __**INACTIVE**__.")
    lprint(ctx, "Fetched server status.")

@bot.command()
async def motd(ctx, *message):
    if message:
        message = format_args(message)
        server_functions.edit_properties('motd', message)
        await ctx.send("Message of the day updates!")
        lprint("Updated motd: " + message)
    else: await ctx.send(server_functions.edit_properties('motd')[1])

@bot.command()
async def start(ctx):
    if server_functions.start_minecraft_server():
        await ctx.send("***Booting Server...***")
    else: await ctx.send("**Error** starting server, contact administrator!")
    time.sleep(5)
    await ctx.send("***Fetching server status...***")
    await ctx.invoke(bot.get_command('status'), show_players=False)
    lprint(ctx, "Starting server.")

@bot.command()
async def stop(ctx):
    mc_command('say WARNING | Server will halt in 15s!')
    await ctx.send("***Halting in 15s...***")
    time.sleep(10)
    mc_command('say WARNING | 5s left!')
    time.sleep(5)
    mc_command('stop')
    await ctx.send("World Saved. Server __**HALTED**__")
    lprint(ctx, "Stopping server.")

@bot.command(aliases=['reboot'])
async def restart(ctx):
    lprint(ctx, "Restarting server.")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    time.sleep(5)
    await ctx.invoke(bot.get_command('start'))

@bot.command(aliases=['backups', 'worldsaves'])
async def saves(ctx, amount=5):
    embed = discord.Embed(title='World Backups')
    worlds = server_functions.fetch_worlds(amount)
    for save in worlds:
        embed.add_field(name=worlds.index(save), value=f"`{save}`", inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?restore <index>` to restore world save.")
    await ctx.send("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")
    lprint(ctx, f"Fetched {amount} most recent world saves.")

@bot.command(aliases=['backupworld', 'worldbackup'])
async def backup(ctx, *name):
    if not name:
        await ctx.send("Hey! I need a name or keywords to make a backup!")
        return

    name = format_args(name)
    mc_command(f"say INFO | Standby, world is currently being archived. Codename: {name}")
    await ctx.send("***Saving current world...***")
    mc_command(f"save-all")
    time.sleep(5)
    backup = server_functions.backup_world(name)
    if backup:
        await ctx.send(f"Cloned and archived your world to:\n`{backup}`.")
    else: await ctx.send("**Error** saving the world! || it's doomed!||")
    await ctx.invoke(bot.get_command('saves'))
    lprint(ctx, "New backup: " + backup)

@bot.command(aliases=['restoreworld', 'worldrestore'])
async def restore(ctx, index=None):
    try: index = int(index)
    except:
        await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
        return

    restore = server_functions.get_world_from_index(index)
    lprint(ctx, "Restoring to: " + restore)
    await ctx.send(f"***Restoring...*** `{restore}`")
    mc_command(f"say WARNING | Initiating jump to save point in 5s! | {restore}")
    time.sleep(5)

    # Stops server if running
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_world(restore)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

@bot.command('deleteworld')
async def delete(ctx, index):
    try: index = int(index)
    except:
        await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
        return

    to_delete = server_functions.get_world_from_index(index)
    server_functions.delete_world(to_delete)
    await ctx.send(f"World as been incinerated!")
    await ctx.invoke(bot.get_command('saves'))
    lprint(ctx, "Deleted: " + to_delete)

@bot.command(aliases=['rebirth', 'hades'])
async def newworld(ctx):
    mc_command("say WARNING | Project Rebirth will commence in T-5s!")
    await ctx.send(":fire:**INCINERATED:**:fire:")
    await ctx.send("**NOTE:** Next startup will take longer, to generate new world. Also, server settings will be preserved, this does not include data like player's gamemode status, inventory, etc.")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_world(reset=True)
    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))
    lprint(ctx, "World Reset.")

# Edit server properties.
@bot.command(aliases=['property'])
async def properties(ctx, target_property='', *value):
    if not target_property:
        await ctx.send("Need at leat property name, optionally input new value to change property.\nUsage example: `?property motd`, `?property motd Hello World!`")
        return

    if not value:
        value = ''
    else: value = ' '.join(value)

    get_property = server_functions.edit_properties(target_property, value)[1]
    await ctx.send(get_property)
    lprint(ctx, f"Server property: {get_property[1:][:-1]}")

@bot.command(aliases=['serverupdate'])
async def update(ctx):
    lprint(ctx, "Updating server.jar...")
    await ctx.send("***Updating...***")
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    time.sleep(5)
    await ctx.send("***Downloading latest server.jar***")
    server = server_functions.download_new_server()
    if server:
        await ctx.send(f"Downloaded latest version: `{server}`")
        time.sleep(3)
        await ctx.invoke(bot.get_command('start'))
    else: await ctx.send("**Error:** Updating server. Suggest restoring from a backup.")
    lprint(ctx, "Server Updated.")

@bot.command(aliases=['serverbackups'])
async def serversaves(ctx, amount=5):
    embed = discord.Embed(title='Server Backups')
    servers = server_functions.fetch_servers(amount)
    for save in servers:
        embed.add_field(name=servers.index(save), value=f"`{save}`", inline=False)

    await ctx.send(embed=embed)
    await ctx.send("Use `?serverrestore <index>` to restore server.")
    await ctx.send("**WARNING:** Restore will overwrite current server. Make a backup using `?serverbackup <codename>`.")
    lprint(ctx, f"Fetched latest {amount} world saves.")

@bot.command(aliases=['backupserver'])
async def serverbackup(ctx, *name):
    if not name:
        await ctx.send("Hey! I need a name or keywords to make a backup!")
        return

    name = format_args(name)
    await ctx.send("***Backing Up...***")

    mc_command(f"save-all")
    time.sleep(5)
    backup = server_functions.backup_server(name)

    if backup:
        await ctx.send(f"New backup:\n`{backup}`.")
    else: await ctx.send("**Error** saving server!")

    await ctx.invoke(bot.get_command('servers'))
    lprint(ctx, "New backup: " + backup)

@bot.command(aliases=['restoreserver'])
async def serverrestore(ctx, index=None):
    try: index = int(index)
    except:
        await ctx.send("I need a index number of world to restore, use `?saves` to get list of saves")
        return

    restore = server_functions.get_server_from_index(index)
    lprint(ctx, "Restoring to: " + restore)
    await ctx.send(f"***Restoring...*** `{restore}`")
    mc_command(f"say WARNING | Initiating jump to save point in 5s! | {restore}")
    time.sleep(5)

    # Stops server if running
    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))

    if server_functions.restore_server(restore):
        await ctx.send("Server **Restored!**")
    else: await ctx.send("**Error:** Could not restore server!")

    time.sleep(3)
    await ctx.invoke(bot.get_command('start'))

@bot.command()
async def serverdelete(ctx, index):
    try: index = int(index)
    except:
        await ctx.send("Need a index number of world to obliterate, use `?saves` to get list of saves")
        return

    to_delete = server_functions.get_server_from_index(index)
    server_functions.delete_server(to_delete)
    await ctx.send(f"Server backup deleted!")
    await ctx.invoke(bot.get_command('servers'))
    lprint(ctx, "Deleted: " + to_delete)

@bot.command(aliases=['resetserver'])
async def serverreset(ctx):
    mc_command("say WARNING | Resetting server in 5s!")
    await ctx.send("**Resetting Server...**")
    await ctx.send("**NOTE:** Next startup will take longer, to setup server and generate new world. Also `server.properties` file will reset!")

    if get_server_status():
        await ctx.invoke(bot.get_command('stop'))
    server_functions.restore_server(reset=True)

    time.sleep(5)
    await ctx.invoke(bot.get_command('start'))
    lprint(ctx, "Server Reset.")

@bot.command()
async def onlinemode(ctx, mode=''):
    if mode not in ['true', 'false']:
        await ctx.send(server_functions.edit_properties('online-mode')[1])
        await ctx.send("Need `true` or `false` argument to change online-mode property.")
        return

    server_functions.edit_properties('online-mode', mode)
    await ctx.send(server_functions.edit_properties('online-mode')[1])
    await ctx.send("Restart server to apply change.")
    lprint(ctx, "Updated online-mode: " + mode)

@bot.command(aliases=['log'])
async def serverlog(ctx, lines=5):
    log_data = server_functions.get_output(file_path=server_functions.server_log_file, lines=lines)
    await ctx.send(f"`{log_data}`")
    lprint(ctx, f"Fetched {lines} lines from bot log.")

# Restarts this bot script.
@bot.command(aliases=['rbot', 'rebootbot'])
async def restartbot(ctx):
    os.chdir(server_functions.server_functions_path)
    await ctx.send("***Rebooting Bot...***")
    lprint(ctx, "Restarting bot.")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.command()
async def rcon(ctx, state=''):
    response = server_functions.edit_properties('enable-rcon', state)[1]
    await ctx.send(response)


@bot.command()
async def botlog(ctx, lines=5):
    log_data = server_functions.get_output(file_path=server_functions.bot_log_file, lines=lines)
    await ctx.send(f"`{log_data}`")
    lprint(ctx, f"Fetched {lines} lines from log.")


@bot.remove_command("help")
@bot.command()
async def help(ctx):
    lprint(ctx, "Fetched help page.")
    current_command, embed_page, contents = 0, 1, []
    pages, current_page, page_limit = 3, 1, 15

    def new_embed(page):
        return discord.Embed(title=f'Help Page {page}/{pages}')

    embed = new_embed(embed_page)
    for command in server_functions.get_csv('command_info.csv'):
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

if __name__ == '__main__':
    bot.run(TOKEN)
