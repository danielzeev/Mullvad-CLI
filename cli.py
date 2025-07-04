import argparse
from ops import DEFAULT_RELAYS
from ops import (
    add_default_relay, swap_default_relays, remove_default_relay,
    print_defaults, handle_up, handle_down, check_relay_status, 
    update_database, fetch_relay_info, query_database, print_query_results,
    move_default_relay
)

def build_parser():

    # Initialize the argument parser and Subparser
    parser = argparse.ArgumentParser(description="mull")

    ## ---------- Subcommands ----------- ##

    subparsers = parser.add_subparsers(title="Commands")

    # 'up' subcommand to activate the relay
    up_parser = subparsers.add_parser('up', help="Activate relay")
    up_relay_group = up_parser.add_mutually_exclusive_group()
    up_relay_group.add_argument('relay', type=str, nargs='?', help="Relay hostname to activate")
    up_relay_group.add_argument('-r', '--results', type=int, metavar='N', help="Use relay at index N from query results")
    up_parser.add_argument('-v', '--verbose', action='store_true', help='Enable output from wg-quick')
    up_parser.set_defaults(func=handle_up, action='up')

    # 'down' subcommand to deactivate the relay
    down_parser = subparsers.add_parser('down', help="Deactivate relay")
    down_parser.add_argument('-v', '--verbose', action='store_true', help='Enable output from wg-quick')
    down_parser.set_defaults(func=handle_down, action='down')

    # 'add' subcommand to add a new relay to the default relay list either by appending or inserting at pos <idx>
    add_parser = subparsers.add_parser('add', help="Add relay hostname to default relays list", aliases=['a'])
    add_relay_group = add_parser.add_mutually_exclusive_group(required=True)
    add_relay_group.add_argument('relay', type=str, nargs='?', help="Relay hostname to add")
    add_relay_group.add_argument('-r', '--results', type=int, metavar='N', help="Add relay at index N from query results")
    add_parser.add_argument('-p', '--position', metavar='P', type=int, help="Index position (P) to insert relay")
    add_parser.set_defaults(func=add_default_relay)

    # 'remove' subcommand to remove a relay from the default relay list
    remove_parser = subparsers.add_parser('remove', help="Remove a relay from default relays list (hostname or position)")
    remove_parser.add_argument('relay', type=str, help="Relay to remove (hostname or idx position, 0 is first position)")
    remove_parser.set_defaults(func=remove_default_relay)

    # 'swap' subcommand to swap relays positions within the default relay list
    swap_parser = subparsers.add_parser('swap', help="Swap position of two relays within the default relays list")
    swap_parser.add_argument('index1', type=int, help="First relay's index to swap")
    swap_parser.add_argument('index2', type=int, help="Second relay's index to swap")
    swap_parser.set_defaults(func=swap_default_relays)

    # 'move' subcommand to swap relays positions within the default relay list
    move_parser = subparsers.add_parser('move', help="Move relay to another index position in the default relay list")
    move_parser.add_argument('index1', type=int, help="Relay index to move")
    move_parser.add_argument('index2', type=int, help="Index position to insert")
    move_parser.set_defaults(func=move_default_relay)

    # 'defaults' subcommand to print the default relay list - display other data?
    defaults_parser = subparsers.add_parser('defaults', help="Print default relays list (aliases: 'd')", aliases=['d'])
    defaults_parser.set_defaults(func=print_defaults)

    # 'update' subcommand to update the servers (relays) database
    update_parser = subparsers.add_parser('update', help="Update the server database")
    update_parser.set_defaults(func=update_database)

    # 'info' subcommand to get database info for a specific relay
    info_parser = subparsers.add_parser('info', help="Display info for a specific relay", aliases=['i'])
    info_relay_group = info_parser.add_mutually_exclusive_group(required=True)
    info_relay_group.add_argument('relay', type=str, nargs='?', help="Relay hostname to show info for")
    info_relay_group.add_argument('-r', '--results', type=int, metavar='N', help="Show info for relay at index N from query results")
    info_parser.add_argument('-v', '--verbose', action='store_true', help="Print additional relay data")
    info_parser.set_defaults(func=fetch_relay_info)

    # 'results' subcommand to print the hostnames from the saved query results
    results_parser = subparsers.add_parser('results', help='Print hostname results from saved query')
    results_parser.set_defaults(func=print_query_results)

    # 'status' subcommand to get connection info for a specific relay
    status_parser = subparsers.add_parser('status', help='Check the connection status of a relay')
    status_parser.add_argument('-v', '--verbose', action='store_true', help="Print additional relay data")
    status_parser.set_defaults(func=check_relay_status)

    # 'query' subcommand to query the database
    query_parser = subparsers.add_parser('query', help="Query database, see `query -h` for options", aliases=["q"])
    
    country_help = "Country filter. Country code (2-letter) or name, accepts partial string search"
    city_help    = "City filter. City code (3-letter) or name, accepts partial string search"
    daita_help   = "Defense Against AI-guided Traffic Analysis, choices = [0, 1]"

    query_args = {
        "country":   {"flags": ["-C", "--country"], "type": str,  "help": country_help, "metavar": ""},
        "city":      {"flags": ["-c", "--city"],    "type": str,  "help": city_help, "metavar": ""},
        "provider":  {"flags": ["--provider"],      "type": str,  "help": "Provider filter", "metavar": ""},
        "active":    {"flags": ["--active"],        "type": int,  "choices": [0, 1], "help": "Active status, choices = [0, 1]", "metavar": ""},
        "owned":     {"flags": ["--owned"],         "type": int,  "choices": [0, 1], "help": "Ownership status, choices = [0, 1]", "metavar": ""},
        "daita":     {"flags": ["--daita"],         "type": int,  "choices": [0, 1], "help": daita_help, "metavar": ""},
    }        
    # Add arguments    
    for name, options in query_args.items():
        flags = options.pop("flags")
        query_parser.add_argument(*flags, **options)

    # Set defaults
    query_parser.set_defaults(func=query_database)

    return parser