# Putting Lord Unga on a server

Everything here assumes a fresh Ubuntu box with a normal user who has `sudo`.
On Oracle Cloud that user is `ubuntu`.

## The whole thing

```bash
git clone https://github.com/AliRidaAtie/troglodyte-os.git
cd troglodyte-os
bash deploy/setup.sh
nano .env                # paste the Discord token and the Gemini key
sudo systemctl restart troglodyte
tail -f troglodyte.log
```

You want to see `[+] Lord Unga#7768 online. 26 commands registered.`

## What setup.sh does

- installs python3-venv, pip, git and nano
- builds a virtualenv in `.venv` and installs `requirements.txt` into it
- copies `.env.example` to `.env` if there isn't one already
- writes a systemd unit at `/etc/systemd/system/troglodyte.service`
- enables it, so the bot comes back on its own after a reboot
- sets `Restart=always`, so it comes back on its own after a crash
- sends all output to `troglodyte.log` next to the code

## Day to day

| | |
|---|---|
| `tail -f troglodyte.log` | watch it live |
| `sudo systemctl status troglodyte` | is it up |
| `sudo systemctl restart troglodyte` | after editing `.env` |
| `git pull && sudo systemctl restart troglodyte` | deploy a code change |
| `sudo systemctl stop troglodyte` | take it offline |

## The data file

`troglodyte_data.json` sits next to the code and holds every Bone, the museum,
the trivia memory and the criminal record. It is in `.gitignore`, so it is never
committed and a `git pull` will not touch it. Back it up if the museum fills with
anything good:

```bash
cp troglodyte_data.json ~/troglodyte_data.$(date +%F).json
```

## One thing to watch on Oracle's free tier

Oracle reserves the right to reclaim an Always Free instance that stays under 20%
CPU **and** under 20% network for seven days straight. A Discord bot is quiet, so
this is worth knowing about rather than ignoring. Check on it now and again:

```bash
uptime
sudo systemctl status troglodyte
```

If the instance ever does disappear, nothing is lost that a fresh box and this
script cannot rebuild in ten minutes, provided you kept a copy of the data file.
