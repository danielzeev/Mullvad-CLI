# Mullvad-CLI Documentation

Mullvad-CLI was built to make managing Mullvad VPN connections on Linux faster and more convenient. Instead of manually typing `# wg-quick up <relay>` to activate a connection, this tool lets you maintain a favorites list, activate relays instantly, and handle everything from a clean command-line interface. It also includes torrent protection to prevent accidental VPN shutdown while torrenting, and maintains a local relay database for fast filtering and selection.

---

## Table of Contents

- [Features](#features)  
- [Requirements](#requirements)  
- [Installation](#installation)  
- [Database](#database)  
- [Commands Reference](#commands-reference)  
  - [Relay Defaults Management](#relay-defaults-management)  
  - [Relay Activation & Deactivation](#relay-activation--deactivation)  
  - [Information and Status Commands](#information-and-status-commands)  
  - [Advanced Query](#advanced-query)  
- [Additional Information](#additional-information)

---

## Features

- Activate or deactivate Mullvad relays  
- Manage default relay list: add, remove, and swap relays  
- View relay information and connection status  
- Maintain and query a local SQLite database of Mullvad servers  
- Automatic deactivation protection during torrenting  
- No external Python dependencies — runs on default Python installation  

> **Note:** See the end of `defaults.conf` to add torrent clients if yours is missing.

---

## Requirements

- Python 3.6+ (standard library only)  
- SQLite3 (usually bundled with Python)  
- `wg` and `wg-quick` from WireGuard ([install instructions](https://www.wireguard.com/install/))  
- Linux system (tested on [Void Linux](https://voidlinux.org/))  
- WireGuard config files located in `/etc/wireguard/` as per [wg-quick man pages](https://www.man7.org/linux/man-pages/man8/wg-quick.8.html)  

---

## Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/danielzeev/Mullvad-CLI.git
   ````

2. Make the `mull` script executable:

   ```bash
   cd Mullvad-CLI
   chmod +x mull
   ```
3. Make the `mull` command accessible globally by creating a symlink to a directory in your `PATH` (e.g., `~/bin` or `/usr/local/bin`):

   Check if `~/bin` is in your path:

   ```bash
   echo $PATH
   ```

   If not, add it in your shell config file (`.bashrc`, `.zshrc`, etc.):

   ```bash
   export PATH="$HOME/bin:$PATH"
   ```

   Create the symlink:

   ```bash
   ln -s /full/path/to/Mullvad-CLI/mull ~/bin/mull
   ```
4. Run `mull` from anywhere:

   ```bash
   mull <subcommand>
   ```

---

## Database

Mullvad-CLI maintains a local SQLite database of Mullvad servers to enable fast queries and server selection. Update it with:

```bash
mull update
```

---

## Commands Reference

### Relay Defaults Management

* **`defaults`**
  Show the current default (favorites) relay list:

  ```bash
  mull defaults
  ```

* **`add`**
  Add a relay to the default list:

  ```bash
  mull add [options] <relay>
  ```

  * `relay`: Relay hostname to add

  *Options:*

  * `-r, --results N`  : Add relay at index `N` from query results
  * `-p, --position P` : Index position (P) to insert relay

  *Example:*

  ```bash
  mull add se-mma-wg-001          # Append relay  
  mull add se-mma-wg-001 -p 2     # Insert at index 2
  mull add --results 2            # Appends the relay located at index 2 in the query results
  mull add -r 2                   # Appends the relay located at index 2 in the query results
  mull add -r 2 -p 1              # Insert the relay located at index 2 in the query results to position 1 in the defaults list
  ```

* **`remove`**
  Remove a relay by hostname or index:

  ```bash
  mull remove [options] <relay>
  ```

  *Example:*

  ```bash
  mull remove se-mma-wg-001       # Remove by hostname  
  mull remove 2                   # Remove by index
  ```

* **`move`**
  Move relay from one index to another in the default list:

  ```bash
  mull move <index1> <index2>
  ```

  *Example:*

  ```bash
  mull move 1 3                   # Move relay from index 1 to index 3
  ```

* **`swap`**
  Swap positions of two relays in the default list:

  ```bash
  mull swap <index1> <index2>
  ```

  *Example:*

  ```bash
  mull swap 1 3                   # Swap relays at index 1 and 3
  ```

---

### Relay Activation & Deactivation

* **`up`**
  Activate a relay:

  ```bash
  mull up [options] <relay>
  ```

  * If no relay specified, activates the first relay in the default list.
  * `<relay>` can be hostname or index.

  *Options:*

  * `-r, --results N`: Use relay at index `N` from query results
  * `-v, --verbose`  : Show detailed `wg-quick` output
  
  *Examples:*

  ```bash
  mull up                         # Activate first default relay  
  mull up 1                       # Activate relay at index 1  
  mull up se-mma-wg-001           # Activate by hostname
  mull up --results 1             # Activate relay located at index 1 from the query results   
  mull up -r 1                    # Activate relay located at index 1 from the query results
  ```

* **`down`**
  Deactivate a relay:

  ```bash
  mull down [options]
  ```

    *Options:*

  * `-v, --verbose`: Show detailed `wg-quick` output

  *Examples:*

  ```bash
  mull down                      # Deactivate relay  
  mull down -v                   # Deactivate relay and display `wg-quick` output
  mull -v down                   # Deactivate relay and display `wg-quick` output
  ```

> **Note:** Torrent activity is detected by scanning running processes via `ps aux` for torrent clients listed in `defaults.conf`.

---

### Information and Status Commands

* **`update`**
  Refresh the local Mullvad server database:

  ```bash
  mull update
  ```

* **`info`**
  Show detailed information about a relay:

  ```bash
  mull info [options] <relay>
  ```
  
  *Options:*

  * `-v, --verbose`     : Show extended details
  * `-r, --results N`   : Use relay at index `N` from query results
 
  *Examples:*

  ```bash
  mull info 1                       # Show info for relay at index 1 in the default list
  mull info se-mma-wg-001           # Show info for relay se-mma-wg-001
  mull info --results 1             # Show info for relay located at index 1 from the query results   
  mull info -r 1                    # Show info for relay located at index 1 from the query results
  mull info -r 1 -v                 # Show extended info for relay located at index 1 from the query results
  ```

* **`status`**
  Get connection info from mullvad check and WireGuard status (when used with `-v` flag):

  ```bash
  mull status
  ```

---

### Advanced Query

* **`query`**
  Filter and list servers from the database:

  ```bash
  mull query [options]
  ```

  *Options:*

  ```
   -h, --help                  : Show the help message and exit
   -C, --country  <code|name>  : Filter by country code or name
   -c, --city     <code|name>  : Filter by city code or name
   --provider     <name>       : Filter by provider
   --active       <0|1>        : Filter by active status
   --owned        <0|1>        : Filter by ownership
   --daita        <0|1>        : Filter by DAITA enabled status
  ```
  
  *Examples:*

  ```bash
  mull query --country usa                # Search for relays from USA
  mull query -C usa                       # Search for relays from USA
  mull query --country usa --city miami   # Search for relays from Miami, USA
  mull query -C usa -c miami              # Search for relays from Miami, USA
  mull query -c miami                     # Search for relays from Miami, USA
  mull query --active 1                   # Search for active (server on) relays
  mull query --owned 0                    # Search for servers not owned by Mullvad  
  ```

> **Notes on `--country` and `--city`:**
>    - If the provided `--country` argument is exactly two letters, it is assumed to be a country code and will be matched against the `country_code` column.
>    - If the `--city` argument is exactly three letters, it is treated as a city code and matched against the `city_code` column.
>    - Otherwise, the inputs are treated as partial names and matched using SQL `LIKE` against `country_name` or `city_name` depending on the flag used.

---

## Additional Information

* See the `defaults.conf` file for torrent clients monitored to prevent accidental VPN shutdown during torrenting.
* The project is designed for easy extensibility and minimal dependencies.