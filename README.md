### Control Minecraft server with Discord bot.

Executes server.jar in detached tmux session, bot runs in 2nd window of said session.
Utializes tmux send-key command to pass through command to server.

#### Requirements:
- [Python3](https://www.python.org/)
- [Tmux](https://github.com/tmux/tmux/wiki)
- [Java 64bit](https://www.java.com/en/download/linux_manual.jsp)
- For Windows: [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

#### Python Modules:
- [discord.py](https://github.com/Rapptz/discord.py)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [psutil](https://pypi.org/project/psutil/)
- [file-read-backwards](https://pypi.org/project/file-read-backwards/)

#### Setup Virtualenv:
Create Python environment:
```bash
virtualenv ~/pyenv/minecraft_discord_bot
```
Activate new Python env:
```bash
source ~/pyenv/minecraft_discord_bot/bin/activate
```
Install required Python modules:
```bash
pip3 install discord bs4 psutil file-read-backwards
```

### Initial Startup:
1. Setup Discord token file, then update `discord_bot_token_file` variable in `server_functions.py`.
2. In `server_functions.py` update directory paths and file paths variables as needed.
3. Run `server_functions.py` with Python3 to start tmux session, discord_mc_bot and setup needed directories.
4. A) If already have Minecraft server move, contents to `/server` folder created by the script, then use `?start` command in discord.\
B) Or use `?update` to download latest server.jar file from official Minecraft website. eula.txt will be updated automatically.
