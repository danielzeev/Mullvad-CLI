import configparser
import subprocess
import sqlite3
import sys
import re
import os

## ------------- LOAD DEFAULTS FROM CONF FILE ------------- ##

from config import (
    CONFIG, BASE_DIR, CONFIG_PATH,
    DATABASE_PATH, DEFAULT_RELAYS,
    INIT_DB_PATH, TORRENT_CLIENTS
    )

QUERY_RESULTS_FILE_PATH = "./query_results.txt"
LEN_DEFAULTS = len(DEFAULT_RELAYS)

## ------------- UTILITY FUNCTIONS ------------- ##

def _validate_relay(relay):
    '''
    Ensures relay str is in the right format (ab-cde-fg-123).
    '''
    pattern = r'^[a-zA-Z]{2}-[a-zA-Z]{3}-[a-zA-Z]{2}-\d{3}$'    
    return re.match(pattern, relay)


def _write_relays_to_conf(DEFAULT_RELAYS):
    '''
    Writes default relays to .conf file.
    '''
    CONFIG['RELAYS'] = {i:relay for i, relay in enumerate(DEFAULT_RELAYS)}
    with open(CONFIG_PATH, 'w') as configfile:
        CONFIG.write(configfile)   
        
def _green_str(string):
    return f"\033[32m{string}\033[0m"

def _red_str(string):
    return f"\033[31m{string}\033[0m"

def _orange_str(string):
    return f"\033[38;5;214m{string}\033[0m"

def _blue_str(string):
    return f"\033[34m{string}\033[0m"

def _yellow_str(string):
    # return f"\033[33m{string}\033[0m" # dull yellow
    return f"\033[93m{string}\033[0m" # bright yellow


def _resolve_relay_argument(args):
    """
    Helper function to resolve relay from either direct name, defaults index, or results index.
    """
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
    '''
    Adds relay to default relay list and saves list to .conf file.
    '''
    relay = _resolve_relay_argument(args)
    
    if _validate_relay(relay):
        if relay in DEFAULT_RELAYS:
            print(f"Relay `{relay}` already in list")
            exit()
        elif isinstance(args.position, int):
            DEFAULT_RELAYS.insert(args.position, relay)
        else:
            DEFAULT_RELAYS.append(relay.lower())                    
        _write_relays_to_conf(DEFAULT_RELAYS) 
        print(_green_str(f"`{relay}` added successfully"))
    else:
        print(f"[ERROR] Cannot append to default list, `{relay}` is not in the right format (ab-cde-fg-123)")


def remove_default_relay(args):
    '''
    Removes relay from default relay list and saves list to .conf file.
    '''
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
    '''
    Swaps index position of two relays in the default relay list and saves list to .conf file.
    '''
    idx1, idx2 = args.index1, args.index2
    try:
        DEFAULT_RELAYS[idx1], DEFAULT_RELAYS[idx2] = DEFAULT_RELAYS[idx2], DEFAULT_RELAYS[idx1]
        print(_green_str(f"Swaped relays at positions {idx1} and {idx2}."))
        _write_relays_to_conf(DEFAULT_RELAYS)
    except IndexError:
        print("Invalid indices. Ensure they are within range.")  


def print_defaults(args):
    '''
    Prints the default relays
    '''    
    if len(DEFAULT_RELAYS):
        for i, relay in enumerate(DEFAULT_RELAYS):
            print(f"{i} : {relay}")
    else:
        print("No default relays found, add relay using `append <relay>`")



## ------------- ACTIVATE / DEACTIVATE & CONNECTION INFO ------------- ##

def _is_integer(string):
    '''Check if string is an (+-) integer'''
    return True if re.match(r"^-?\d+$", string) else False

def _fetch_relay_from_defaults(relay): #digit
    '''Fetch relay from default list using digit and return as list.''' 
    idx = int(relay)
    if idx < LEN_DEFAULTS:
        return DEFAULT_RELAYS[idx] 
    else:
        print(f"[ERROR] `{idx}` is larger than items in list `{LEN_DEFAULTS}`")
        exit()

def _get_active_relays():
    '''
    Returns all the active interfaces (relays) via `wg show`.
    '''
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

def _is_torrenting():
    '''
    Check for running torrent software.
    '''
    try:
        ps_output = subprocess.check_output(['ps', 'aux'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running 'ps aux': {e}", file=sys.stderr) # using sys.stderr bc not part of running shell command
        return "error"

    for client in TORRENT_CLIENTS:
        if client.lower() in ps_output.lower():
            return True
    return False


def handle_relay(args):
    '''
    Activate / Deactive a relay, or deactivate all activated relays (with --all flag).
    ex: mull down --all
    ''' 
    relay = _resolve_relay_argument(args)

    if args.action == 'up':

        if relay is None:
            if LEN_DEFAULTS:
                relay = DEFAULT_RELAYS[0]
            else:
                print("Must provide a relay hostname if there are no relays in the defaults list")
                exit()                
        elif _is_integer(relay):
            relay = _fetch_relay_from_defaults(relay)

        relays = [relay]

    elif args.action == 'down':    
        
        if relay is not None:       # Hostname provided
            if _is_integer(relay):   
                relays = [_fetch_relay_from_defaults(relay)]
            else:
                relays = [relay]
        else:                       # No hostname provided
            interfaces = _get_active_relays()
            if interfaces:
                if getattr(args, 'all'): # multiple interfaces active
                    relays = interfaces[::-1]
                else:
                    relays = [interfaces[-1]]
            else:
                print("No active relays detected")
                exit() 
        
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
                exit() 
   
    # Activate / Deactivate
    for relay in relays:
        
        if _validate_relay(relay): 
            try:
                result = subprocess.run(
                    ['sudo', 'wg-quick', args.action, relay],
                    stdout=subprocess.PIPE,   # Capture stdout
                    stderr=subprocess.STDOUT, # Combine stderr with stdout
                    text=True,                # Get output as text (string)
                    check=True                # Raise CalledProcessError if command fails
                )
        
                print(_green_str(f"{'Activated' if args.action == 'up' else 'Deactivated'}: {relay}"))                
                
                if args.verbose: 
                    print(result.stdout)  # prints `wg-quick` output

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] wg-quick failed with code {e.returncode}")
                print(f"Output: {e.output or e.stdout}")
                print(f"Error:  {e.stderr or 'No error output available'}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                # traceback.print_exc() # need import traceback
        else:
            print(f"[ERROR] `{relay}` is not in the right format (ab-cde-fg-123)")


def check_relay_status(args):
    '''
    Checks relay status via `wg show`.
    '''
    # `args` here can be a str (if coming from `list_active_relays()`) or Namespace 
    # `args.relay` can be a list if called from `status` subcommand or str
    relay = (
        args if isinstance(args, str) 
        else args.relay[0] if isinstance(args.relay, list) 
        else args.relay
    )
    
    if relay is None:
        print("[STATUS ERROR] no relay provided, must provide hostname")
        print("[INFO] to get status of all active relays `mull active --status`")
        exit()

    if not _validate_relay(relay):
        print(f"[STATUS ERROR] `{relay}` is not in the right format (ab-cde-fg-123)")
        exit()
        
    try:
        result = subprocess.run(
            ['sudo', 'wg', 'show', relay],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.returncode == 0:
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)
            print()
        else:
            print(f"[STATUS ERROR] Could not retrieve status for `{relay}`")
            print(f"[WG] {result.stdout}")

    except Exception as e:
        print(f"Unexpected error checking status: {e}")


def list_active_relays(args):
    '''
    Lists all active relays.
    '''
    interfaces = _get_active_relays()
    
    if not interfaces:
        print("No active WireGuard interfaces.")
    else:
        # print("Active Relays:\n")
        for iface in interfaces:
            print(f"🟢 {iface}")
            if args.status:
                check_relay_status(iface)



## ------------- DATABASE FETCHING AND QUERYING ------------- ##
   
def _get_connection():
    '''
    Connects to local database where Mullvad server info is stored.
    '''
    conn = sqlite3.connect(DATABASE_PATH) # 'relays.db'
    conn.row_factory = sqlite3.Row # if doing this for all queries (reutrns a column : value)
    return conn


def _print_query_col_header(default_columns: dict):
    '''Prints the query column names.'''
    print(
        ''.join(f"{col.upper():<{width}} " 
        for col, width in default_columns.items())
        )

def _print_query_row_values(row_query_dict: dict, default_columns: dict):
    '''Prints single row from query result.'''
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
    '''
    Writes sqlite query result hostnames to file.
    '''
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
        exit()
    return hostnames[index]


def print_query_results(args=None):
    '''Prints saved query results (hostnames).''' 
    hostnames = _load_query_results()
    header_cols = {"IDX": 4, "hostname": 13}
    _print_query_col_header(header_cols)    
    for idx, relay in enumerate(hostnames):        
        print(f"{idx:<4} {_yellow_str(relay):<13}")


def update_database(args=None):
    '''
    Fetches the current Mullvad server information and updates local database.
    '''
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
    '''
    Fetch server info for hostname.    
    '''
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
        exit()

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
        exit()

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
        exit()

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