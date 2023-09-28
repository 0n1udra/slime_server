## Control Minecraft server with Discord bot.  
Scroll down for requirements, setup instructions and screenshots.  

- Join Discord server for bot help: https://discord.gg/s58XgzhE3U
- See releases: https://github.com/0n1udra/slime_server/releases  
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
5. Run `python3 run_bot.py help`, shows commands to setup tmux and/or run bot.
  - `python3 run_bot.py setup` - Create required folders if starting from scratch.
  - `python3 run_bot.py startbot` - Starts bot.
  - `python3 run_bot.py attachbot` - Attach to tmux/screen if using.
  - `python3 run_bot.py startbot attachtmux`
6. Use `?setchannel` or `?sc` command to set channel id. This is optional, any command issued to the bot will update the channel_id, however you may not see an output for that command until reissued.
7. Read through the help pages with `?help` or `?help2` in Discord.
8. Optionals:
  - Use `?serverscan` command to add servers you manually put in the 'servers' folder.
  - You can use `?update` to download latest .jar file (Downloads latest PaperMC by default, more details in `slime_vars.py` comments, line 63)


### User Configs
- use_pyenv:


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

