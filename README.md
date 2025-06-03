# 🛡️ Mullvad-CLI: Mullvad CLI Wrapper for WireGuard (Linux)

A lightweight command-line Python interface to manage Mullvad VPN connections using WireGuard on Linux systems. Designed for Linux distros where the Mullvad app is **_not_** officially supported.

See the [Examples](#🔎-examples) section below for usage demonstrations

Mullvad-CLI was built to make managing Mullvad VPN connections on Linux faster and more convenient. Instead of manually typing `# wg-quick up <relay>` to activate a connection, this tool lets you maintain a favorites list, activate relays instantly, and handle everything from a clean command-line interface. It also includes torrent protection to prevent accidental VPN shutdown while torrenting, and maintains a local relay database for fast filtering and selection.

---

## ✨ Features

- ⚡ Activate or deactivate Mullvad relays  
- ➕ Add, remove, and swap relays in the default relay list  
- ℹ️ View relay information and status  
- 💾 Maintain and query a local SQLite database of Mullvad servers  
- 🛑 Deactivation protection when torrenting  
- 🐍 No external Python dependencies — runs on default Python installation  

> **Note:** Check the end of `defaults.conf` for torrent clients, add yours if it's not there.  
> Currently checks for: `qbittorrent | transmission | deluge | fragments | ktorrent`

---

## 🖥️ Requirements

- Python 3.6+ (standard library only)  
- SQLite3 (usually included with Python)  
- `wg`, `wg-quick` (from WireGuard) — [install instructions](https://www.wireguard.com/install/)  
- Linux system (tested on [Void Linux](https://voidlinux.org/))  
- WireGuard config files saved in `/etc/wireguard/` ([man pages](https://www.man7.org/linux/man-pages/man8/wg-quick.8.html))

---

## 🚀 Installation

1. **Clone the repo:**

```bash
git clone https://github.com/danielzeev/Mullvad-CLI.git
````

2. **Make the `mull` script executable:**

```bash
cd Mullvad-CLI
chmod +x mull
```

3. **Make `mull` accessible globally:**

You can save the directory anywhere, but to run `mull` from anywhere, symlink it to a directory in your `PATH` (e.g., `~/bin` or `/usr/local/bin`).

* Check your `PATH`:

```bash
echo $PATH
```

* Add `~/bin` to your `PATH` if missing (add this to `.bashrc` or `.zshrc`):

```bash
export PATH="$HOME/bin:$PATH"
```

* Create the symlink:

```bash
ln -s /full/path/to/Mullvad-CLI/mull ~/bin/mull
```

Now you can run:

```bash
mull <subcommand>
```

---

## 🗄️ Database

The script maintains a local SQLite database of Mullvad servers for fast querying and server selection.
Run:

```bash
mull update
```

to refresh the database.

---

## 🧰 Usage

```bash
Commands:  
    up                  Activate relay  
    down                Deactivate relay  
    defaults (d)        Print default relays list
    add (a)             Add relay hostname to default relays list  
    remove              Remove a relay (hostname or position)  
    swap                Swap position of two relays in default list  
    move                Move relay to another index position in the default relay list  
    update              Update the server database  
    info (i)            Display info for a relay  
    status              Check relay connection status  
    results             Print hostnames from query
    query (q)           Query database with filters  

Query Options:  
    -C, --country       Country filter (code or name, partial match allowed)  
    -c, --city          City filter (code or name, partial match allowed)  
    --provider          Provider filter  
    --active            Active status (0 or 1)  
    --owned             Ownership status (0 or 1)  
    --daita             DAITA enabled (0 or 1)  
```

See [Documentation](documentation.md) for detailed command info.

---


## 🔎 Examples

### Handling Relays

![Handle Relay](assets/handle_relay.gif)

### Relay Info

![Info](assets/info.gif)

### Relay Status

![Status](status/info.gif)

### Query Database

![Query](assets/query.gif)

### Pass Query Results to Command

![Results](assets/results.gif)

### Torrenting Prompt for VPN Shutdown

![Torrenting](assets/torrenting.gif)
