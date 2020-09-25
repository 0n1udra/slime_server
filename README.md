## Control Minecraft server with Discord bot.

Executes server.jar in detached tmux session, bot runs in 2nd window of said session.
Utializes tmux send-key command to pass through command to server.

### Versions:
#### Local with Tmux:
If you have access to the Minecraft server and server related files/folders.
There are functions that backup/restore world folder and even the whole server folder, and there's also functions that edit server files like server.properties and eula.txt.
Tmux is used to pass commands through to Minecraft server, and is also used to capture and log server output.
bs4 is used for server update function by downloading latest server.jar file from official Minecraft website.

#### RCON:
Control Minecraft server with RCON, you only have access to server functions and won't be able to edit server files/folders like backup/restore world saves or edit server properties.


## Local with Tmux
### Requirements:
- [Python3](https://www.python.org/)
- [Tmux](https://github.com/tmux/tmux/wiki)
- [Java 64bit](https://www.java.com/en/download/linux_manual.jsp)
- For Windows: [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

### Python Modules:
- [discord.py](https://github.com/Rapptz/discord.py)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [file-read-backwards](https://pypi.org/project/file-read-backwards/)


### Initial Startup:
1. Setup Discord token file, then update `discord_bot_token_file` variable in `server_functions.py`.
2. In `server_functions.py` update directory paths and file paths variables as needed.
3. Run `server_functions.py setup` with Python3 to start tmux session, discord_mc_bot and setup needed directories.
4. A) If already have Minecraft server move, contents to `/server` folder created by the script, then use `?start` command in discord.\
B) Or use `?update` to download latest server.jar file from official Minecraft website. eula.txt will be updated automatically.
5. Read through the help page with `?help`.

## RCON
### Python Modules:
- [discord.py](https://github.com/Rapptz/discord.py)
- [mctools](https://pypi.org/project/mctools/)

### Initial Startup:
1. Create a RCON password file containg your server's RCON password, then in `server_functions.py` update RCON and other variables as needed.
2. Read through the help page with `?help`.

### Using Virtualenv:
Create Python environment:
```bash
virtualenv ~/pyenv/minecraft_discord_bot
```
Activate new Python env:
```bash
source ~/pyenv/minecraft_discord_bot/bin/activate
```
Install required Python modules (Local version):
```bash
pip3 install discord bs4 file-read-backwards
```
(RCON):
```bash
pip3 install discord bs4 file-read-backwards
```
