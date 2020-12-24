## Control Minecraft server with Discord bot.
Minecraft Discord bot server control. 

See [releases](https://github.com/0n1udra/slime_server/releases).

### Features:
- Basic commands: say, kick, teleport, save, weather, and gamemode.
- Online players, banned, OP list, whitelist, and ban.
- World save backup and restore system. Also has server folder backup/restore feature. These features need direct access to server files.
- Server start, stop, status, version, log, update server.jar, and edit server.properties
- RCON Support. Need direct access to files, Tmux or subprocess for some features.

### Requirements:
- [Python3](https://www.python.org/)
- [Java 64bit](https://www.java.com/en/download/linux_manual.jsp)
- [Tmux](https://github.com/tmux/tmux/wiki) (Optionaal)
- [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10) (Optional)

### Python Modules:
- [discord.py](https://github.com/Rapptz/discord.py)
- [asyncio](https://docs.python.org/3/library/asyncio.html), [time](https://docs.python.org/3/library/time.html)

Extra Modules:
- [subprocess](https://docs.python.org/3/library/subprocess.html), [fileinput](https://docs.python.org/3/library/fileinput.html), [requests](https://pypi.org/project/requests/), [shutil](https://docs.python.org/3/library/shutil.html), [json](https://docs.python.org/3/library/json.html), [csv](https://docs.python.org/3/library/csv.html), [sys](https://docs.python.org/3/library/sys.html), [os](https://docs.python.org/3/library/os.html), [re](https://docs.python.org/3/library/re.html)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [file-read-backwards](https://pypi.org/project/file-read-backwards/)
- [mctools](https:  //pypi.org/project/mctools/) (RCON)


### Initial Startup:
1. Create Discord bot using this [portal](https://discord.com/developers/applications).
2. Update `slime_vars.py` variables.
3. Run `python3 run_bot.py help` for how to setup, or run `discord_mc_bot.py` directly.
4. Read through the help pages with `?help` or `?help2` in Discord.

## Using Virtualenv:
Create Python Virtualenvt:
```bash
virtualenv ~/pyenv/minecraft_discord_bot
```
Activate new Python Virtualenv:
```bash
source ~/pyenv/minecraft_discord_bot/bin/activate
```
Install required Python modules:
```bash
pip3 install discord asyncio file-read-backwards mctools
```

