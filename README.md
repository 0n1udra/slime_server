## Control Minecraft server with Discord bot.
#### Branch for button and list functionalty with discord-components module.

[Releases](https://github.com/0n1udra/slime_server/releases)

<img width="800" alt="Screen Shot 2021-12-04 at 22 33 54" src="https://user-images.githubusercontent.com/15573136/144732439-82c696df-56c9-4024-b93b-30d78958cfa3.png">

<img width="800" alt="Screen Shot 2021-12-04 at 22 57 41" src="https://user-images.githubusercontent.com/15573136/144732861-278016b7-e3f8-44ba-8352-10a9f1d3438e.png">



### Features:
- Basic commands: say, kick, teleport, save, weather, and gamemode.
- Show online players, banned, OP list, and whitelist.
- World save backup and restore system. Also has server folder backup/restore feature. These features need direct access to server files.
- Server autosave, start, stop, status, version, log, update server.jar, and edit server.properties
- Interface via RCON, Tmux or subprocess. Some features and command may be disabled if using RCON or Subprocess.

### Requirements:
- [Python3](https://www.python.org/)
- [Java 64bit](https://www.java.com/en/download/linux_manual.jsp) (If hosting Minecraft server)
- [Tmux](https://github.com/tmux/tmux/wiki) (If hosting Minecraft server)
- [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) (If on Windows)

### Python Modules:
- [discord.py](https://github.com/Rapptz/discord.py)
- [discord-components](https://pypi.org/project/discord-components/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [file-read-backwards](https://pypi.org/project/file-read-backwards/) (Needed for reading server log file (for now))
- [mctools](https://pypi.org/project/mctools/) (If using RCON)
- [subprocess](https://docs.python.org/3/library/subprocess.html), [requests](https://pypi.org/project/requests/), [datetime](https://docs.python.org/3/library/datetime.html), [random](https://docs.python.org/3/library/random.html), [json](https://docs.python.org/3/library/json.html), [csv](https://docs.python.org/3/library/csv.html), [sys](https://docs.python.org/3/library/sys.html), [os](https://docs.python.org/3/library/os.html), [re](https://docs.python.org/3/library/re.html)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) (For `?serverupdate` feature)


### Setup:
1. Create Discord bot using this [portal](https://discord.com/developers/applications).
2. Update `slime_vars.py` variables.
3. Run `python3 run_bot.py help` to setup tmux and/or run bot.
4. Use `?setchannel` command so you get important bot/server event updates.
5. Read through the help pages with `?help` or `?help2` in Discord.

## Using Virtualenv or venv:
Create Python Virtualenvt:
```bash
python venv ~/pyenv/minecraft_discord_bot
```
or
```bash
virtualenv ~/pyenvs/minecraft_discord_bot

```
Activate new Python Virtualenv:
```bash
source ~/pyenvs/minecraft_discord_bot/bin/activate
```
Install required Python modules:
```bash
pip install discord asyncio file-read-backwards mctools
```
or
```bash
pip install -r requirements.txt
```

