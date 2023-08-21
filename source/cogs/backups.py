import asyncio
from os.path import join

import discord
from discord.ext import commands

from bot_files.slime_backend import backend
from bot_files.slime_config import config
from bot_files.slime_utils import lprint, file_utils, utils
from bot_files.discord_components import comps


start_button = [['Start Server', 'serverstart', '\U0001F680']]

class World_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['worldbackupslist', 'backuplist' 'backupslist', 'wbl'])
    async def worldbackups(self, ctx, amount=10):
        """
        Show world backups.

        Args:
            amount optional default(10): Number of most recent backups to show.

        Usage:
            ?saves
            ?saves 15
        """

        worlds = file_utils.enum_dirs_for_discord(config.get_config('world_backups_path'), 'd')
        lprint(ctx, f"Fetched {amount} world saves")
        if worlds is False:
            await backend.send_msg("No world backups found.")
            return

        embed = discord.Embed(title='World Backups :floppy_disk:')
        for backup in worlds[-amount:]:
            embed.add_field(name=backup[3], value=f"`{backup[0]}`", inline=False)
        await backend.send_msg(embed=embed)
        await backend.send_msg("Use `?worldrestore <index>` to restore world save.")
        await backend.send_msg("**WARNING:** Restore will overwrite current world. Make a backup using `?backup <codename>`.")

    @commands.command(aliases=['backupworld', 'newworldbackup', 'worldbackupnew', 'wbn'])
    async def worldbackup(self, ctx, *name):
        """
        new backup of current world.

        Args:
            name: Keywords or codename for new save. No quotes needed.

        Usage:
            ?backup everything not on fire
            ?backup Jan checkpoint
        """

        if not name:
            await backend.send_msg("Usage: `?worldbackup <name>`\nExample: `?worldbackup Before the reckoning`")
            return
        name = utils.format_args(name)

        await backend.send_msg("***Creating World Backup...*** :new::floppy_disk:")
        lprint(ctx, f"INFO: Creating world backup: {name}")

        # Gives server some time to save world.
        await backend.send_command(f"save-all")
        await asyncio.sleep(config.get_config('save_world_wait_time'))

        if new_backup := await backend.new_backup(name, mode='world'):
            await backend.send_msg(f"**New World Backup:** `{new_backup}`")
            await ctx.invoke(self.bot.get_command('worldbackupslist'))
            lprint(ctx, "New world backup: " + new_backup)
        else:
            await backend.send_msg("**ERROR:** Problem saving the world! || it's doomed!||")
            lprint(ctx, "ERROR: Could not world backup: " + name)
            return

        if comps.get_data('server_panel_components'):
            await ctx.invoke(self.bot.get_command('_update_control_panel'), 'world_backups')  # Updates panel if open

    @commands.command(aliases=['wbdate', 'wbnd'])
    async def worldbackupdate(self, ctx):
        """Creates world backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('worldbackup'), '')

    @commands.command(aliases=['restoreworld', 'worldbackuprestore', 'wbr'])
    async def worldrestore(self, ctx, index='', now=''):
        """
        Restore a world backup.

        Args:
            index: Get index with ?worldbackups command.
            now optional: Skip 15s wait to stop server. E.g. ?restore 0 now

        Usage:
            ?restore 3
            ?wbr 5 now

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        if index == 'bmode':  # If this command triggered from a bmode.
            index = comps.get_data('second_selected')
        try: index = int(index)
        except:
            await backend.send_msg("Usage: `?worldrestore <index> [now]`\nExample: `?worldrestore 0 now`")
            return
        if not index: return

        fetched_restore = file_utils.get_from_index(config.get_config('world_backups_path'), index, 'd')
        await backend.send_msg("***Restoring World...*** :floppy_disk::leftwards_arrow_with_hook:")
        lprint(ctx, f"INFO: Restoring world from backup: {fetched_restore}")
        if await backend.send_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}"):
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        if not await backend.restore_backup(fetched_restore, join(config.get_config('server_path'), 'world')):
            await backend.send_msg(f"**Error:** Issue restoring world: {fetched_restore}")
            lprint(ctx, "ERROR: World restore: " + fetched_restore)
            return

        await backend.send_msg(f"**Restored World:** `{fetched_restore}`")
        lprint(ctx, "World restored: " + fetched_restore)
        await asyncio.sleep(5)
        await backend.send_msg("Start server with `?start` or click bmode", view=comps.new_buttons(start_button))

    @commands.command(aliases=['deleteworld', 'wbd'])
    async def worldbackupdelete(self, ctx, index=''):
        """
        Delete a world backup.

        Args:
            index: Index number of the backup to delete. Get number with ?worldbackups command.

        Usage:
            ?delete 0
        """

        if index == 'bmode':
            index = comps.get_data('second_selected')
        try: index = int(index)
        except:
            await backend.send_msg("Usage: `?worldbackupdelete <index>`\nExample: `?wbd 1`")
            return

        to_delete = file_utils.get_from_index(config.get_config('world_backups_path'), index, 'd')
        lprint(ctx, f"INFO: Deleting world backup {to_delete}")
        if not to_delete:
            await backend.send_msg("No backup was selected.")
            return

        if file_utils.delete_dir(to_delete):
            await backend.send_msg(f"**World Backup Deleted:** `{to_delete}`")
            lprint(ctx, "INFO: Deleted world backup: " + to_delete)
        else:
            await backend.send_msg(f"**Error:** Issue deleting: `{to_delete}`")
            lprint(ctx, "ERROR: Deleting world backup: " + to_delete)

        if comps.get_data('server_panel_components'):
            await ctx.invoke(self.bot.get_command('_update_control_panel'), 'world_backups')  # Updates panel if open

    @commands.command(aliases=['rebirth', 'hades', 'resetworld'])
    async def worldreset(self, ctx, now=''):
        """
        Deletes world save (does not touch other server files).

        Args:
            now optional: No 5s warning before resetting.

        Usage:
            ?worldreset
            ?hades now

        Note: This will not make a backup beforehand, suggest doing so with ?backup command.
        """

        if await backend.send_command("say ---WARNING--- Project Rebirth will commence in T-5s!"):
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        await backend.send_msg(":fire: **Project Rebirth Commencing** :fire:")
        await backend.send_msg("**NOTE:** Next launch may take longer.")
        lprint(ctx, f"INFO: Resetting world")

        if file_utils.delete_dir(join(config.get_config('server_path'), 'world')) is False:
            await backend.send_msg("Error trying to reset world.")
            lprint(ctx, "ERROR: Issue deleting world folder.")
        else:
            await backend.send_msg("**Finished.**")
            await backend.send_msg("You can now start the server with `?start`.")
            lprint(ctx, "World Reset")


class Server_Backups(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(aliases=['serverbackupslist', 'sbl'])
    async def serverbackups(self, ctx, amount=10):
        """
        List server backups.

        Args:
            amount default(5): How many most recent backups to show.

        Usage:
            ?serversaves - Shows 10
            ?serversaves 15
        """

        servers = file_utils.enum_dirs_for_discord(config.get_config('server_backups_path'), 'd')
        lprint(ctx, f"Fetched {amount} world backups")
        if servers is False:
            await backend.send_msg("No server backups found.")
            return

        embed = discord.Embed(title='Server Backups :floppy_disk:')
        for save in servers[-amount:]:
            embed.add_field(name=save[3], value=f"`{save[0]}`", inline=False)
        await backend.send_msg(embed=embed)

        await backend.send_msg("Use `?serverrestore <index>` to restore server.")
        await backend.send_msg("**WARNING:** Restore will overwrite current server. Create backup using `?serverbackup <codename>`.")

    @commands.command(aliases=['backupserver', 'newserverbackup', 'serverbackupnew', 'sbn'])
    async def serverbackup(self, ctx, *name):
        """
        New backup of server files (not just world save).

        Args:
            name: Keyword or codename for save.

        Usage:
            ?serverbackup Dec checkpoint
        """

        if not name:
            await backend.send_msg("Usage: `?serverbackup <name>`\nExample: `?serverbackup Everything just dandy`")
            return

        name = utils.format_args(name)
        lprint(ctx, f"Creating new server backup {name}")
        await backend.send_msg(f"***Creating Server Backup...*** :new::floppy_disk:")
        if await backend.send_command(f"save-all"): await asyncio.sleep(3)

        if new_backup := await backend.new_backup(name, mode='server'):
            await backend.send_msg(f"**New Server Backup:** `{new_backup}`")
            await ctx.invoke(self.bot.get_command('serverbackupslist'))
            lprint(ctx, "New server backup: " + new_backup)
        else:
            await backend.send_msg("**ERROR:** Server backup failed! :interrobang:")
            lprint(ctx, "ERROR: Could not server backup: " + name)
            return

        if comps.get_data('server_panel_components'):
            await ctx.invoke(self.bot.get_command('_update_control_panel'), 'server_backups')  # Updates panel if open

    @commands.command(aliases=['sbdate'])
    async def serverbackupdate(self, ctx):
        """Creates server backup with current date and time as name."""

        await ctx.invoke(self.bot.get_command('serverbackup'), '')

    @commands.command(aliases=['restoreserver', 'serverbackuprestore', 'restoreserverbackup', 'sbr'])
    async def serverrestore(self, ctx, index='', now=''):
        """
        Restore server backup.

        Args:
            index: Number of the backup to restore. Get number from ?serversaves command.
            now optional: Stop server without 15s wait.

        Usage:
            ?serverrestore 0
            ?sbr 1 now
        """

        if index == 'bmode':
            index = comps.get_data('second_selected')
        try: index = int(index)
        except:
            await backend.send_msg("Usage: `?serverrestore <index> [now]`\nExample: `?serverrestore 2 now`")
            return
        if not index: return

        fetched_restore = file_utils.get_from_index(config.get_config('server_backups_path'), index, 'd')
        lprint(ctx, f"Restoring server from backup: {fetched_restore}")
        await backend.send_msg(f"***Restoring Server...*** :floppy_disk::leftwards_arrow_with_hook:")

        if await backend.send_command(f"say ---WARNING--- Initiating jump to save point in 5s! : {fetched_restore}"):
            await asyncio.sleep(5)
            await ctx.invoke(self.bot.get_command('serverstop'), now=now)

        try: await backend.restore_backup(fetched_restore, config.get_config('server_path'))
        except:
            await backend.send_msg("**ERROR:** Could not restore server!")
            lprint(ctx, "ERROR: Server restore: " + fetched_restore)
            return

        await backend.send_msg(f"**Server Restored:** `{fetched_restore}`")
        await backend.send_msg("Start server with `?start` or click bmode", view=comps.new_buttons(start_button))
        lprint(ctx, "Server restored: " + fetched_restore)

    @commands.command(aliases=['deleteserverrestore', 'serverdeletebackup', 'serverrestoredelete', 'sbd'])
    async def serverbackupdelete(self, ctx, index=''):
        """
        Delete a server backup.

        Args:
            index: Index of server save, get with ?serversaves command.

        Usage:
            ?serverbackupdelete 0
            ?sbd 5
        """

        if index == 'bmode':  # If this command triggered from a bmode.
            index = comps.get_data('second_selected')
        try: index = int(index)
        except:
            await backend.send_msg("Usage: `?serverbackupdelete <index>`\nExample: `?sbd 3`")
            return

        to_delete = file_utils.get_from_index(config.get_config('server_backups_path'), index, 'd')
        lprint(ctx, f"Deleting server backup: {to_delete}")
        if not to_delete:
            await backend.send_msg("No backup was selected.")
            return

        if file_utils.delete_dir(to_delete):
            await backend.send_msg(f"**Server Backup Deleted:** `{to_delete}`")
            lprint(ctx, "Deleted server backup: " + to_delete)
        else:
            await backend.send_msg(f"**Error:** Issue deleting: `{to_delete}`")
            lprint(ctx, "ERROR: Deleting server backup: " + to_delete)

        if comps.get_data('server_panel_components'):
            await ctx.invoke(self.bot.get_command('_update_control_panel'), 'server_backups')  # Updates panel if open

async def setup(bot):
    await bot.add_cog(World_Backups(bot))
    await bot.add_cog(Server_Backups(bot))
