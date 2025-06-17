import configparser
import subprocess
import requests
import sqlite3
import sys
import re
import os

## ------------- LOAD DEFAULTS FROM CONF FILE ------------- ##

from config import (
    CONFIG, BASE_DIR, CONFIG_PATH,
    DATABASE_PATH, DEFAULT_RELAYS,
    INIT_DB_PATH, TORRENT_CLIENTS,
    QUERY_RESULTS_FILE_PATH
    )


LEN_DEFAULTS = len(DEFAULT_RELAYS)

## ------------- UTILITY FUNCTIONS ------------- ##

def _validate_relay(relay):
    """
    Ensures relay str is in the right format.
    `ab-cde-fg-123` for single hop
    `abcd123-efgh456` for multi hop
    """
    single = r'^[a-zA-Z]{2}-[a-zA-Z]{3}-[a-zA-Z]{2}-\d{3}$'
    multi  = r'^[a-z]{4}\d{3}-[a-z]{4}\d{3}$'
    return re.match(single, relay) or re.match(multi, relay)

def _write_relays_to_conf(DEFAULT_RELAYS):
    """Writes default relays to .conf file."""
    CONFIG['RELAYS'] = {i:relay for i, relay in enumerate(DEFAULT_RELAYS)}
    with open(CONFIG_PATH, 'w') as configfile:
        CONFIG.write(configfile)   

def _is_integer(string):
    """Check if string is an (+-) integer."""
    return True if re.match(r"^-?\d+$", string) else False
  
def _fetch_relay_from_defaults(relay): #digit
    """Fetch relay from default (favorites) list using idx.""" 
    idx = int(relay)
    if idx < LEN_DEFAULTS:
        return DEFAULT_RELAYS[idx] 
    else:
        print(f"[ERROR] `{idx}` is larger than items in list `{LEN_DEFAULTS}`")
        sys.exit()

def _green_str(string):
    return f"\033[32m{string}\033[0m"

def _yellow_str(string):
    # return f"\033[33m{string}\033[0m" # dull yellow
    return f"\033[93m{string}\033[0m" # bright yellow

def _orange_str(string):
    return f"\033[38;5;214m{string}\033[0m"

# def _red_str(string):
#     return f"\033[31m{string}\033[0m"

# def _blue_str(string):
#     return f"\033[34m{string}\033[0m"


def _resolve_relay_argument(args):
    """Helper function to resolve relay from either direct name, defaults index, or results index."""
    if hasattr(args, 'results') and args.results is not None:
        return _get_relay_from_results(args.results)
    elif hasattr(args, 'relay') and args.relay is not None:
        if _is_integer(args.relay):
            relay = _fetch_relay_from_defaults(args.relay)
        else:
            relay = args.relay
        return relay
    else:
        return None  # Let the original command handle missing relay


## ------------- VIEWING & MODIFYING DEFAULT RELAYS ------------- ##


def add_default_relay(args):
    """Adds relay to default relay list and saves list to .conf file."""
    relay = _resolve_relay_argument(args)

    if _validate_relay(relay):
        if relay in DEFAULT_RELAYS:
            print(f"Relay `{relay}` already in list")
            sys.exit()
        elif args.position is not None and isinstance(args.position, int):
            DEFAULT_RELAYS.insert(args.position, relay)
        else:
            DEFAULT_RELAYS.append(relay.lower())                    
        _write_relays_to_conf(DEFAULT_RELAYS) 
        print(_green_str(f"`{relay}` added successfully"))
    else:
        print(f"[ERROR] Cannot append to default list, `{relay}` is not in the right format (ab-cde-fg-123)")


def remove_default_relay(args):
    """Removes relay from default relay list and saves list to .conf file."""
    relay = args.relay
    len_defaults = len(DEFAULT_RELAYS)
    if relay.isdigit():
        relay = int(relay)
        if relay < len_defaults:
            relay = DEFAULT_RELAYS.pop(relay)
            _write_relays_to_conf(DEFAULT_RELAYS)   # save to conf
            print(_green_str(f"Relay `{relay}` removed successfully."))
        else:
            print("list index out of range")    
    elif _validate_relay(relay):
        DEFAULT_RELAYS.remove(relay)
        _write_relays_to_conf(DEFAULT_RELAYS)       # save to conf
        print(_green_str(f"Relay `{relay}` removed successfully."))    
    else:
        print(f"Relay `{relay}` not found.")

def swap_default_relays(args):
    """Swaps index position of two relays in the default relay list and saves list to .conf file."""

    idx1, idx2 = args.index1, args.index2
    try:
        DEFAULT_RELAYS[idx1], DEFAULT_RELAYS[idx2] = DEFAULT_RELAYS[idx2], DEFAULT_RELAYS[idx1]
        print(_green_str(f"Swaped relays at positions {idx1} and {idx2}."))
        _write_relays_to_conf(DEFAULT_RELAYS)
    except IndexError:
        print("Invalid indices. Ensure they are within range.")  

def move_default_relay(args):
    """Move relay to another index position in the default relay list."""
    try:
        DEFAULT_RELAYS.insert(args.index2, DEFAULT_RELAYS.pop(args.index1))
        print(_green_str(f"Moved relay at position {args.index1} to {args.index2}."))
        _write_relays_to_conf(DEFAULT_RELAYS)
    except IndexError:
        print("Invalid indices. Ensure they are within range.") 

def print_defaults(args):
    """Prints the default relays."""    
    if len(DEFAULT_RELAYS):
        for i, relay in enumerate(DEFAULT_RELAYS):
            print(f"{i} : {relay}")
    else:
        print("No default relays found, add relay using `append <relay>`")



## ------------- CONNECTION INFO ------------- ##

def _get_active_relays():
    """Returns all active interface (relay) via `wg show`."""
    print("Getting active relays, sudo password may be required...")
    try:
        result = subprocess.run(
            ['sudo', 'wg', 'show', 'interfaces'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        interfaces = result.stdout.strip().split()
        return interfaces
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to get interfaces: {e.stdout.strip()}")
    except Exception as e:
        print(f"Unexpected error: {e}")  

def _get_mullvad_connection_check_info():
    """Returns mullvad connection check info."""
    MULLVAD_CHECK_URL = "https://am.i.mullvad.net/json"
    try:
        response = requests.get(MULLVAD_CHECK_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching relays data: {e}")
        exit(1)

def _print_connection_check_info(response):
    """Print output of mullvad connection check: https://mullvad.net/en/check."""
    keys = [
        'ip', 'country', 'city', 'mullvad_exit_ip', 
        'mullvad_exit_ip_hostname', 'blacklisted', 'organization'
        ]
    key_width = 18
    for key in keys:
        val = response.get(key, 'Key not found')
        if key == 'blacklisted':
            val = val['blacklisted']
        elif key == 'mullvad_exit_ip_hostname':
            key = 'mullvad_hostname'
        padded_key = f"{key:<{key_width}}" 
        print(f"{_yellow_str(padded_key)}: {val}")


def check_relay_status(args): 
    """Checks relay status via mullvad api and `wg show` when used with `-v` flag."""
    response = _get_mullvad_connection_check_info()
    if not response.get('mullvad_exit_ip'):
        print("No active relay found")
        sys.exit()    
    else:
        _print_connection_check_info(response)
        
        if args.verbose:
            relay = response.get('mullvad_exit_ip_hostname')

            if not _validate_relay(relay):
                print(f"[FORMAT ERROR] `{relay}` is not in the right format (ab-cde-fg-123)")
                sys.exit()
                
            try:
                result = subprocess.run(
                    ['sudo', 'wg', 'show', relay],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                if result.returncode == 0:
                    print()
                    print("-" * 60)
                    print(result.stdout)
                    print("-" * 60)
                else:
                    print(f"[STATUS ERROR] Could not retrieve status for `{relay}`")
                    print(f"[WG] {result.stdout}")

            except Exception as e:
                print(f"Unexpected error checking status: {e}")

## ------------- ACTIVATE / DEACTIVATE RELAYS ------------- ##

def _is_torrenting():
    """Check for running torrent software."""
    try:
        ps_output = subprocess.check_output(['ps', 'aux'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running 'ps aux': {e}", file=sys.stderr) # using sys.stderr bc not part of running shell command
        return "error"

    for client in TORRENT_CLIENTS:
        if client.lower() in ps_output.lower():
            return True
    return False


def _handle_relay(args, relay):
    """Handles activation/deactivation of relay."""
    msg = {'up' : 'Activated', 'down' : 'Deactivated'}

    if _validate_relay(relay): 
        try:
            result = subprocess.run(
                ['sudo', 'wg-quick', args.action, relay],
                stdout=subprocess.PIPE,   # Capture stdout
                stderr=subprocess.STDOUT, # Combine stderr with stdout
                text=True,                # Get output as text (string)
                check=True                # Raise CalledProcessError if command fails
            )

            print(_green_str(f"{msg[args.action]}: {relay}"))                
            
            if args.verbose: 
                print(result.stdout)  # prints `wg-quick` output

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] wg-quick failed with code {e.returncode}")
            print(f"Output: {e.output or e.stdout}")
            print(f"Error:  {e.stderr or 'No error output available'}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print(f"[FORMAT ERROR] `{relay}` is not in the right format (ab-cde-fg-123)")


def handle_up(args):
    """Connect to relay."""
    connection_info = _get_mullvad_connection_check_info()
    if connection_info.get('mullvad_exit_ip'):
        print("A relay is already active, please deactivate first using `mull down`")
        sys.exit()

    relay = _resolve_relay_argument(args)
    
    # Fallback to default relay if no relay was provided
    if not relay:
        if DEFAULT_RELAYS:
            relay = DEFAULT_RELAYS[0]
        else:
            print("No relay specified and no defaults available. Provide a relay hostname.")
            sys.exit(1)
    
    _handle_relay(args, relay)
    

def handle_down(args):
    """Disconnects active relay."""
    # Double check user wants to deactivate when torrenting
    torrenting = _is_torrenting()
    if torrenting:
        s = {
            True   : "Torrenting detected, are you sure you want to deactivate VPN? y/n ",            
            "error": "An error occured while trying to detect torrenting activity, continue to deactivate VPN? y/n "
        }[torrenting]
        user_input = input(_orange_str(s))
        if user_input != 'y':
            print("Exiting...")
            sys.exit() 

    interfaces = _get_active_relays()
    if interfaces:
        relay = interfaces[0]
        _handle_relay(args, relay) # Deactivate
    else:
        print("No active relays detected")
        sys.exit()         


## ------------- DATABASE FETCHING AND QUERYING ------------- ##
   
def _get_connection():
    """Connects to local database where Mullvad server info is stored."""
    conn = sqlite3.connect(DATABASE_PATH) # 'relays.db'
    conn.row_factory = sqlite3.Row # if doing this for all queries (reutrns a column : value)
    return conn


def _print_query_col_header(default_columns: dict):
    """Prints the query column names."""
    print(
        ''.join(f"{col.upper():<{width}} " 
        for col, width in default_columns.items())
        )

def _print_query_row_values(row_query_dict: dict, default_columns: dict):
    """Prints single row from query result."""
    vals = []
    for col, val in row_query_dict.items():
        width = default_columns[col]
        if val is not None:
            if col == 'hostname':
                val = _yellow_str(val)
                vals.append(f"{val:<{width}} ")                
            else:
                vals.append(f"{val:<{width}} ")                
        else:
            vals.append('None ')
    print(''.join(vals))


def _write_query_results(query_results):
    """Writes sqlite query result hostnames to file."""
    with open(QUERY_RESULTS_FILE_PATH, "w") as f:
        hostnames = [result["hostname"] for result in query_results]
        f.write('\n'.join(hostnames))


def _load_query_results(): 
    """Load and return query results from file."""
    if not os.path.exists(QUERY_RESULTS_FILE_PATH):
        raise TypeError(
            f"Query results file not found: {QUERY_RESULTS_FILE_PATH}. Run 'mull query' first."
        )    
    try:
        with open(QUERY_RESULTS_FILE_PATH, 'r') as f:
            hostnames = f.read().splitlines()
    except Exception as e:
        raise TypeError(f"Error reading query results: {e}")
    
    if not isinstance(hostnames, list) or len(hostnames) == 0:
        raise TypeError("No query results available.")
    
    return hostnames


def _get_relay_from_results(index): 
    """Get relay name from query results at specified index."""
    hostnames = _load_query_results()
    if index >= len(hostnames):
        print(f"Index {index} out of range. Available indices: 0-{len(hostnames)-1}")    
        sys.exit()
    return hostnames[index]


def print_query_results(args=None):
    """Prints saved query results (hostnames).""" 
    hostnames = _load_query_results()
    header_cols = {"IDX": 4, "hostname": 13}
    _print_query_col_header(header_cols)    
    for idx, relay in enumerate(hostnames):        
        print(f"{idx:<4} {_yellow_str(relay):<13}")


def update_database(args=None):
    """Fetches the current Mullvad server information and updates local database."""
    try:
        result = subprocess.run(['python', INIT_DB_PATH], capture_output=True, text=True)

        # Check if the script was successful
        if result.returncode == 0:
            print("Database updated successfully")
        else:
            print(f"Error updating database:\n{result.stderr}")

    except Exception as e:
        print(f"Error running the script: {e}")


def fetch_relay_info(args):
    """Fetch server info for hostname."""

    # Columns to print and their output widths
    default_columns = {
        "hostname": 13, "country_name" : 15, "city_name": 20, 
        "active" : 8, "owned" : 6, "daita" : 6, "status_messages" : 1,
        }

    relay = _resolve_relay_argument(args)

    if _is_integer(relay):   
        relay = _fetch_relay_from_defaults(relay)
        default_columns = dict(hostname=13) | default_columns

    conn  = _get_connection()
    cur   = conn.cursor()
    
    # Join the list into a comma-separated string for the SELECT clause
    columns_str = ", ".join(default_columns.keys())
    
    # Default search query
    default_query = f"""
    SELECT {columns_str}
    FROM relays
    WHERE hostname = ?;
    """
    # Execute query
    cur.execute(default_query, (relay,))
    default_results = cur.fetchone()

    if not default_results:
        print("Hostname not found")
        sys.exit()

    # Convert to dict
    default_results = dict(default_results)

    # Print header (column names) and values (server info)
    _print_query_col_header(default_columns)
    _print_query_row_values(default_results, default_columns)
    print()

    # Print additional info
    if args.verbose:

        # Get the list of all column names in relays table
        cur.execute("PRAGMA table_info(relays);")
        all_columns = [col[1] for col in cur.fetchall()]  # col[1] contains the column names
        
        # Exclude the columns from default_columns lists
        additional_cols = [col for col in all_columns if col not in default_columns and col != "hostname"]
        additional_cols = ", ".join(additional_cols)
       
        verbose_query = f"""
        SELECT {additional_cols}
        FROM relays
        WHERE hostname = ?;
        """

        cur.execute(verbose_query, (relay,))
        verbose_results = cur.fetchone()

        # Print additional relay info
        for k, v in dict(verbose_results).items():
            print(f"{k:<22} ",v)
        print()
        
    cur.close()
    conn.close()


def query_database(args):
    """
    Handle general filtering queries (e.g., --country us --city nyc).

    For country and city, can query using either:
    - name (or part of name) 
    - two letter country code

    Note:
    - If the provided `--country` argument is exactly two letters, it is assumed to be a country code and will be matched against the `country_code` column.
    - If the `--city` argument is exactly three letters, it is treated as a city code and matched against the `city_code` column.
    - Otherwise, the inputs are treated as partial names and matched using `LIKE` against `country_name` or `city_name`.
    """
    # Convert Namespace to dict
    namespace_dict = vars(args)

    # for country and city we have `country_name`, `country_code`, `city_name` and `city_code`
    if getattr(args, 'country'):
        country_key = "country_code" if len(args.country) == 2 else "country_name"
        namespace_dict[country_key] = namespace_dict.pop('country')
    
    if getattr(args, 'city'):
        city_key = "city_code" if len(args.city) == 3 else "city_name"
        namespace_dict[city_key] = namespace_dict.pop('city')
    
    # Filter available while removing ['func']
    query_params = {
        k:v for k,v in namespace_dict.items()
        if v is not None and k != 'func'
    }
    
    # Catch empty query
    if not query_params:
        print("No query provided. Exiting...")
        sys.exit()

    # Build the base of the query
    query = "SELECT * FROM relays WHERE "
    
    # Create a list of conditions and values based on the dictionary keys
    conditions = []
    values     = []

    for key, value in query_params.items():
        if key in ['country_name', 'city_name']:
            conditions.append(f"{key} COLLATE NOCASE LIKE ?")
            values.append(f"%{value}%")
        else:
            conditions.append(f"{key} COLLATE NOCASE = ?")
            values.append(value)

    # Join all conditions with 'AND'
    query += " AND ".join(conditions)
    
    # Conect to DB   
    conn = _get_connection()
    cur  = conn.cursor()
    
    # Execute the query with the values from the dictionary
    cur.execute(query, tuple(values))
    
    # Fetch the results
    results = cur.fetchall()
    
    if not results:
        print("No results found matching specified query")
        sys.exit()

    # Columns to print and their output widths 
    default_columns = {
        "IDX": 4, "hostname": 13, "country_name" : 15, "city_name": 20, 
        "active" : 8, "owned" : 6, "daita" : 6, "status_messages" : 1,
        }

    # Print column headers
    _print_query_col_header(default_columns) 

    # Print the results for the default columns
    for idx, row in enumerate(results):
        # Creates `col`:`value` pairs from each Sqlite3.Row object only for desired display columns
        row_data  = {"IDX" : idx} | {col: row[col] for col in default_columns if col in dict(row)}
        # Get column values and combine into a single string
        _print_query_row_values(row_data, default_columns)

    # Write hostname results to file
    _write_query_results(query_results=results)

    # Close the connection
    cur.close()
    conn.close()