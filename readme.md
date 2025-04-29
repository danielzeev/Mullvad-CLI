# mull-cli: Mullvad CLI Wrapper for WireGuard (Linux)
A lightweight command-line Python interface to manage Mullvad VPN connections using WireGuard on Linux systems.
Designed for Linux distros where the Mullvad app is not __officially supported__.

## Features
- Activate or deactivate Mullvad relays
- Add, remove, and swap relays in the default relay list
- View relay information and status
- Maintain and query a local SQLite database of Mullvad servers
- Deactivation protection when torrenting  
- No external Python dependencies — runs on default Python installation

 > Note: check the end of `defaults.conf` for torrent clients, add yours if it's not there
 > checks for: `qbittorrent|transmission|deluge|fragments|ktorrent`


## Requirements
- Python 3.6+ (standard library only)
- SQLite3 (for the relay database), which is usually packaged with the python installation
- wg, wg-quick (from WireGuard), [install instructions](https://www.wireguard.com/install/)
- Linux system (tested on Void Linux)
- Wireguard configuration files (saved in `/etc/wireguard/`) as described in the [man pages](https://www.man7.org/linux/man-pages/man8/wg-quick.8.html)

## Installation
No installation needed. Just clone and run:
1) Clone
```bash
git clone https://github.com/danielzeev/Mullvad-CLI.git
```
2) Make the `mull` script executable
```bash
cd mull-cli
chmod +x mull
```
3) Make `mull` command accessible from anywhere

- You can save the `mull-cli` directory anywhere but you will need to symlink the `mull` file to a directory in your `PATH` like `~/bin/` or `/usr/local/bin/`. 
> If you move to `~/bin/` add this to your shell config (e.g. `.bashrc` or `.zshrc`) if `~/bin/` is not in your `PATH`:
> ```bash
> export PATH="$HOME/bin:$PATH"
> ```

- To __symlink__ to `~/bin`:
```bash
ln -s /full/path/to/mull-cli/mull ~/bin/mull
```

Now you can run:
```bash
mull <subcommand>
```

## Database
The script maintains a local SQLite database of Mullvad servers for fast querying and server selection. Run `mull update` to refresh the database.


## Usage

```
Commands:  
    up                  Activate relay
    down                Deactivate relay
    add (a)             Add relay hostname to default relays list
    remove              Remove a relay from default relays list (hostname or position)
    swap                Swap position of two relays within the default relays list
    defaults (d)        Print default relays list (aliases: 'd')
    update              Update the server database
    info (i)            Display info for a specific relay
    status              Check the status of a relay
    active              List active relays
    query (q)           Query database with filters:

Query Options:
    -C, --country   Country filter (code or name, partial match allowed)
    -c, --city      City filter (code or name, partial match allowed)
    --provider      Provider filter
    --active        Active status (choices: 0, 1)
    --owned         Ownership status (choices: 0, 1)
    --type          Relay type (Wireguard or Bridge)
    --daita         DAITA enabled (Defense Against AI-guided Traffic Analysis; choices: 0, 1)
```
- See [Documentation](documentation.md) for more information on each subcommand


### Handling Relays
![Handle Relay](assets/handle_relay.gif)

### Relay Info
![Info](assets/info.gif)

### Query Database
![query](assets/query.gif)


## License
