# Mullvad-CLI: Mullvad CLI Wrapper for WireGuard (Linux)
A lightweight command-line Python interface to manage Mullvad VPN connections using WireGuard on Linux systems.
Designed for Linux distros where the Mullvad app is not __officially supported__.

## Features
- Activate or deactivate Mullvad relays
- Add, remove, and swap relays in the default relay list
- View relay information and status
- Maintain and query a local SQLite database of Mullvad servers
- Deactivation protection when torrenting 
- No external Python dependencies — runs on default Python installation

> Note: see the end of `defaults.conf` for torrent clients, add yours if it's not there 

## Requirements
- Python 3.6+ (standard library only)
- SQLite3 (for the relay database), which is usually packaged with the python installation
- wg, wg-quick (from WireGuard), [install instructions](https://www.wireguard.com/install/)
- Linux system (tested on [Void Linux](https://voidlinux.org/))
- Wireguard configuration files (saved in `/etc/wireguard/`) as described in the [man pages](https://www.man7.org/linux/man-pages/man8/wg-quick.8.html)

## Installation

1) Clone
```bash
git clone https://github.com/danielzeev/Mullvad-CLI.git
```
2) Make the `mull` script executable
```bash
cd Mullvad-CLI
chmod +x mull
```
3) Make `mull` command accessible from anywhere

You can save the `Mullvad-CLI` directory anywhere but you will need to symlink the `mull` file to a directory in your `PATH` like `~/bin` or `/usr/local/bin`. 
> If you move to `~/bin` make sure it is in your `PATH` (`echo $PATH`). If it’s not, add this to your shell config (e.g. `.bashrc` or `.zshrc`):
> ```bash
> export PATH="$HOME/bin:$PATH"
> ```

To symlink to `~/bin`:
```bash
ln -s /full/path/to/Mullvad-CLI/mull ~/bin/mull
```

Now you can run:
```bash
mull <subcommand>
```

## Database
The script maintains a local SQLite database of Mullvad servers for fast querying and server selection. Run `mull update` to refresh the database.


## Available Commands

### Relay Defaults

- **`defaults`**: Show the default relays list
  ```bash
  mull defaults
  ```
  - **Options**:
    - `-h, --help`: Show help message

- **`add`**: Add a relay to the default list
  ```bash
  mull add [options] <relay> [position]
  ```
  - **Positional Arguments**:
    - `relay`: Relay to add
    - `position`: Optional index position to insert (default: append)
  - **Options**:
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull add se-mma-wg-001    # appends relay to relay list

  mull add se-mma-wg-001 2  # inserts relay into idx 2
  ```

- **`remove`**: Remove a relay from the list
  ```bash
  mull remove [options] <relay>
  ```
  - **Positional Argument**:
    - `relay`: Hostname or index of the relay to remove
  - **Options**:
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull remove se-mma-wg-001  # removes relay from list

  mull remove 2              # removes relay in idx 2
  ```


- **`swap`**: Swap relay positions
  ```bash
  mull swap <index1> <index2>
  ```
  - **Positional Arguments**:
    - `index1`: Index of the first relay
    - `index2`: Index of the second relay
  - **Options**:
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull swap 1 3  # swaps relays at idx 1 and 3
  ```


### Relay Management

- **`up`**: Activate a relay
  ```bash
  mull up [options] <relay>
  ```
  - **Positional Argument**:
    - `relay`: Relay hostname
  - **Options**:
    - `-v, --verbose`: Enable output from `wg-quick`
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull up    # activate first relay in defaults list (position `0`)

  mull up 1  # activate relay in idx position `1`

  mull up se-mma-wg-001  # activate relay
  ```

- **`down`**: Deactivate a relay
  ```bash
  mull down [options] <relay>
  ```
  - **Positional Argument**:
    - `relay`: Relay hostname
  - **Options**:
    - `--all`: Deactivate all active relays
    - `-v, --verbose`: Enable output from `wg-quick`
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull down               # deactivates relay (last in first out)

  mull down 1             # deactivates relay from idx position `1` in default relay list

  mull down se-mma-wg-001 # deactivate relay

  mull down --all         # deactivate all active relays
  ```

### Information & Status

- **`update`**: Update the server database
  ```bash
  mull update
  ```
  - **Options**:
    - `-h, --help`: Show help message

- **`info`**: Display information about a relay
  ```bash
  mull info [options] <relay>
  ```
  - **Positional Argument**:
    - `relay`: Relay hostname
  - **Options**:
    - `-v, --verbose`: Show additional information
    - `-h, --help`: Show help message

- **`status`**: Check the status of a relay
  ```bash
  mull status <relay>
  ```
  - **Positional Argument**:
    - `relay`: Relay hostname
  - **Options**:
    - `-h, --help`: Show help message

- **`active`**: List active relays
  ```bash
  mull active [options]
  ```
  - **Options**:
    - `-s, --status`: Show the status of active relays
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull active --status  # prints status for all active relays using `wg show interfaces`
  ```


### Advanced Filtering & Queries

- **`query`**: Filter and view the database
  ```bash
  mull query [options]
  ```
  - **Options**:
    - `-C, --country <country>`: Filter by country (code or name)
    - `-c, --city <city>`: Filter by city (code or name)
    - `--provider <name>`: Filter by provider name
    - `--active <0|1>`: Filter by active status
    - `--owned <0|1>`: Filter by ownership status
    - `--type <type>`: Filter by relay type (Wireguard or Bridge)
    - `--daita <0|1>`: Filter by Daita (Defense Against AI-guided Traffic Analysis)
    - `-h, --help`: Show help message
  - **Example**
  ```bash
  mull query --country usa

  mull query --active 1      # get all currently operational relays
  ```


> Note: for country and city
>    - If the provided `--country` argument is exactly two letters, it is assumed to be a country code and will be matched against the `country_code` column.
>    - If the `--city` argument is exactly three letters, it is treated as a city code and matched against the `city_code` column.
>    - Otherwise, the inputs are treated as partial names and matched using `LIKE` against `country_name` or `city_name`.

