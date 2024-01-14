## Control Minecraft server with Discord bot.  
Scroll down for requirements, setup instructions and screenshots.  

- Join Discord server for bot help: https://discord.gg/s58XgzhE3U
- See releases (may not have latest code): https://github.com/0n1udra/slime_server/releases  
- Download latest commit (.zip): https://github.com/0n1udra/slime_server/archive/refs/heads/master.zip
- Jump to: [Guide](#setup), [Screenshots](#screenshots), [Support me](#support-me)  

### Features
- Basic commands: say, kick, teleport, save, weather, and gamemode.
- Show connection history, chat log, online players, banned, OP list, and whitelist.
- World save backup and restore system. Also has server folder backup/restore feature. These features need direct access to server files.
- Server autosave, start, stop, status, version, log, update server.jar (only with Vanilla or PaperMC), and edit server.properties
- Interface via RCON, Tmux or subprocess. Some features and command may be disabled if using RCON or Subprocess.

### TODO List
- Discord user and role specific permissions for certain commands and/or command groups.
- Be able to setup and change bot and server settings without having to edit user_config.json file.
- Show command usage for more commands.
 

### Requirements
- [Python 3.8+](https://www.python.org/)
- [Java 64bit](https://www.java.com/en/download/linux_manual.jsp) (If hosting Minecraft server)
- [Tmux](https://github.com/tmux/tmux/wiki) (If hosting Minecraft server)
- [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) (If on Windows)

### Python Modules
- [discord.py 2.0](https://github.com/Rapptz/discord.py)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [file-read-backwards](https://pypi.org/project/file-read-backwards/) (Needed for reading server log file (for now))
- [mctools](https://pypi.org/project/mctools/) (If using RCON)
- [subprocess](https://docs.python.org/3/library/subprocess.html), [requests](https://pypi.org/project/requests/), [datetime](https://docs.python.org/3/library/datetime.html), [fileinput](https://docs.python.org/3.9/library/fileinput.html), [random](https://docs.python.org/3/library/random.html), [gzip](https://docs.python.org/3/library/gzip.html), [json](https://docs.python.org/3/library/json.html), [csv](https://docs.python.org/3/library/csv.html), [sys](https://docs.python.org/3/library/sys.html), [os](https://docs.python.org/3/library/os.html), [re](https://docs.python.org/3/library/re.html)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) (For `?serverupdate` feature)


# Setup
1. Create Discord bot in Discord Developer Portal. Scroll down for instructions or click [here](#create-discord-bot)  
3. Setup Python venv (if using) and install libraries. Scroll down for instructions or click [here](#using-virtualenv-or-venv).  
4. Update settings by editing `user_config.json` variables. Scroll down for more or click [here](#user-configs)  
    - NOTE: JSON file uses double quotes for strings.  
    - Also, Do NOT edit the `example` server config entry.  
5. Run `python3 run_bot.py help`, shows commands to setup tmux and/or run bot.
  - `python3 run_bot.py makefolders` - Create required folders if starting from scratch.
  - `python3 run_bot.py startbot` - Starts bot.
  - `python3 run_bot.py attachbot` - Attach to tmux/screen if using.
  - `python3 run_bot.py startbot attachtmux`
6. Use `?setchannel` or `?sc` command to set channel id. This is optional, any command issued to the bot will update the channel_id, however you may not see an output for that command until reissued.
7. Read through the help pages with `?help` or `?help2` in Discord.
8. Optionals:
  - Use `?serverscan` command to add servers you manually put in the 'servers' folder.
  - You can use `?update` to download latest .jar file (Downloads latest PaperMC by default, more details in `slime_vars.py` comments, line 63)


### Commands  
- `?help`, `?help2` - Help pages. First one is my custom embed layout, second one is default discord.py format.  
- `?start`, `?stop`, `?restart` - Start/stop Minecraft server.  
- `?check` - Check if server is online, and if console is reachable, if able.  
- `?status` - Server information: status, version, motd, address/IP, players online, etc.  
- `?players` - Show names of online players.  
- `?playerpanel` - Common bot commands and functionality using discord.py components.  
- `?teleportpanel` - Easy to use teleport panel. Includes return button to return teleported player to previous position.  
- `?playerlocate` - Get xyz coords of player.   
- `?serverproperties` - Show or edit properties in server.properties file.  
- `?worldbackup`, `?worldrestore`, `?serverbackup`, `?serverrestore` - Manage world and server backups.  
- `?serverlog`, `?chatlog`, `?connectionlog`, `?botlog` - Show logs for: server, just player chats, server connections and bot.  
- `?update` - Update server .jar file.   
  - The bot checks the server name and description configs to determine what flavor of server to get.  
    E.g. If `papermc` is in the server description, it'll get the latest PaperMC jar from official site.  
  - Currently working: vanilla, papermc  
- `?botupdate` - Uses Git CLI to pull the latest update from Master branch.   
   Note: Will not work if there's local changes. Either stash them or use `git restore .` in source folder.  

### User Configs
#### File Structure:
- Either use `python3 run_bot.py makefolders` to create these folders or create your own and update the paths in configs.  
  - Above command will create `Games` folder in your home directory if it doesn't exist. Then `Minecraft`, `servers`, `world_backups`, and `server_backups` inside.   
  
Example folder structure:
```
Home (home_path, e.g. ~/ or C:\Users\0n1udra)
└─ Games
    └─ Minecraft (mc_path)
       ├─ servers (servers_path)
       │  ├─ papernc (server_path, e.g. ~/Games/Minecraft/servers/papermc)
       │  │  └─ server.jar
       │  └─ vanilla
       │     └─ server.jar
       ├─ server_backups
       │  ├─ papermc (server_backups_path)
       │  └─ vanilla
       └─ world_backups
          ├─ papermc (world_backups_path)
          └─ vanilla
 ```

#### Bot Configs:  
- `use_pyenv`, `pyenv_activate_command` - If using python virtual environment.  
- `bot_launch_command` - Set custom arguments when launching bot.  
- `show_sensitive_info` - Show or hide sensitive info in launch banner.  
- `disabled_commands` - Disable specific commands. Must put original command name not aliases if you want to completely disable it.  
- `bot_token_filepath` - Path to Discord token file.  
- `command_prefix`, `case_insensitive` - Discord command prefix, and command case insensitivity.  
- `players_custom_status`, `custom_status_interval` - Show players online and server ping in bot's custom status section.  
  - `use_custom_ping_address`, `custom_ping_address` - Set a custom address for the ping section.  
- `bot_use_tmux`, `bot_tmux_name`, `bot_tmux_pane` - Run bot in a Tmux session. 
  - NOTE: Set `bot_tmux_name` and `server_tmux_name` to the same to run them both in the same session.
    currently only supports the bot and one Minecraft server.  
- `bot_use_screen`, `bot_screen_name` - Run bot in a Screen session.  
- `home_path`, `bot_source_path`, `mc_path`, `servers_path` - Used for setting default configs for bot and servers.  
- `user_config_filepath`, `bot_log_filepath` - Miscellaneous variables needed for bot.  
- `windows_compatibility` - Bot will automatically detect if running on Windows system.
  This is Needed to adapt some commands to work for Windows, like starting Minecraft server.  
- `windows_cmdline_start` - Bot will prefix this to `server_launch_command` to start server.  
- `selected_server`, `init` - More miscellaneous configs needed for bot functionality.   
 
#### Server Configs:
- `server_name`, `server_description`, `server_version` - Basic server info.  
  - NOTE: Bot will try to detect server version. If it doesn't work, you can set it manually. however, it might be overridden by the bot if it successfully detects a version.  
- `server_address`, `server_port` - Server domain/IP and port. Not needed, but some features may not work properly.  
- `server_use_essentialsx` - EssentialX plugin compatibility.   
  - NOTE: Bot will use `pong` command instead of `xp`. See `status_checker_command` below for more.  
- `server_files_access` - If you are running the bot on the same system as the server, and it can access server files.  
  - Needed for some features like world/server backup and restore, editing server.properties file, etc.  
- `server_use_rcon`, `rcon_pass`, `rcon_port` - RCON configs. Uses `server_address`.  
- `server_use_tmux`, `server_tmux_name`, `server_tmux_pane` - Run server in a Tmux session.  
- `server_use_screen`, `server_screen_name` - Run server using Screen.  
- `server_use_subprocess` - Run server using Python's subprocess module.  
  - NOTE: The server will stop if the bot process is interrupted or killed.  
- `server_launch_command` - Command used to start server. 
- `server_launch_path` - Optionally set a custom path to the server executable (usually a `.jar` file).  
- `startup_wait_time` - This is just used to send a Discord message notifying how long the server takes to start.  
- `save_world_wait_time` - Set how long it takes for the server to save the world after sending a `save-all` command.  
- `check_before_command` - Only used if `server_files_access` is true. Sends a command to the server to check if it's reachable before sending actual command.  
  - NOTE: This will clog your logs up. However, disabling this will mean the bot will not be sure if the server is reachable and if commands issued were successful or not.
  - `status_checker_command"` - The command that will be sent to server with a random number, then bot will check server logs to see if it was received.
  E.g. `xp 0.123463246`.
- `command_buffer_time` - The time it takes for the server to run commands. Change this if your server is slower.  
- `enable_autosave`, `autosave_interval` - Send `save-all` command at specified minutes interval.  
- `log_lines_limit` - Set limit to how many log lines bot can read for some commands, like `?chatlog`.  
- `server_path`, `world_backups_path`, `server_backups_path`, `server_logs_path`, `server_log_filepath`, `server_properties_filepath` - Bot will automatically set these based on `mc_path`. 
  You can manually update them.  
- `world_folders` - Specify what world folders to backup.  
- `useful_websites` - For `?links` command, which shows a Discord embed of these links.  
- `server_ip` - Bot will automatically set this if `server_address` is set.  
  

### Create Discord bot
  1. Go to: https://discord.com/developers/applications.  
  2. Create New App:  
    <img width=50% height=50% src="https://github.com/0n1udra/slime_server/assets/15573136/fdcbfbd3-dc44-4d0e-ba4c-f896cc2f94c8">   
  2. Go to OAUTH > URL Generator section to create invite link for the bot:   
    <img width=50% height=50% src="https://github.com/0n1udra/slime_server/assets/15573136/1bf4ab7f-8a5c-4f26-8af1-238862980944">   
  Set the permissions:  
    <img width=50% height=50% src="https://github.com/0n1udra/slime_server/assets/15573136/f09bd87e-ac82-443e-acc5-ef7f44ea1cac">  
  Invite bot to your server:  
    <img width=20% height=20% src="https://github.com/0n1udra/slime_server/assets/15573136/acdb4fda-f77a-4de0-b811-9ca4778e0c09">   
  3. Go to Bot section and get the token if you haven't already:  
    <img width=50% height=50% src="https://github.com/0n1udra/slime_server/assets/15573136/aafdcc20-d622-429d-9551-f25b532657ed">  
  4. While in the Bot section, scroll down and enable Message Content Intents:  
    <img width=50% height=50% src="https://github.com/0n1udra/slime_server/assets/15573136/ab480973-151e-4817-bb71-ba973a962cd2">   


### Using Virtualenv or venv
Install Python3 venv:
```bash
sudo apt install python3-venv -y
```
Create Python Virtualenvt:
```bash
python -m venv ~/pyenvs/slime_server 
```
Activate new Python Virtualenv:
```bash
source ~/pyenvs/slime_server/bin/activate
```
Install required Python modules:
```bash
pip install -r requirements.txt
```


# Screenshots
<img width="800" alt="Screen Shot 2021-12-04 at 22 33 54" src="https://user-images.githubusercontent.com/15573136/144732439-82c696df-56c9-4024-b93b-30d78958cfa3.png">  
<img width="800" alt="Screen Shot 2021-12-04 at 22 57 41" src="https://user-images.githubusercontent.com/15573136/144732861-278016b7-e3f8-44ba-8352-10a9f1d3438e.png">  
<img width="1362" alt="Screen Shot 2022-04-12 at 6 59 20 PM" src="https://user-images.githubusercontent.com/15573136/196075059-da4cc813-9a75-438e-9d6a-629a45fa4764.png">   


# Support me
- PayPal [@dxzt](https://www.paypal.me/dxzt)  
- Venmo [@dxzt550](https://venmo.com/u/dxzt550)  
- Cash App [$DXZT550](https://cash.app/$DXZT550)  

