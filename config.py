"""
Handles configuration loading and shared constants for mull-cli.
"""
import configparser
import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'defaults.conf')
CONFIG      = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


# DATABASE INIT / UPDATE SCRIPT PATH
INIT_DB_PATH = os.path.join(BASE_DIR, 'init_db.py')


# DATABASE PATH - one will be created if not found
try: 
    DATABASE_PATH = CONFIG['DATABASE']['relay_database_path']
    DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_PATH)
except: 
    print("[config.py] Database path not found in `defaults.conf`")
    DATABASE_PATH = os.path.join(BASE_DIR, 'relays.db')
    print(f"[config.py] creating database path at {DATABASE_PATH}")  # maybe move this to the after writing

    # Create section if it doesn't exist
    if not CONFIG.has_section("DATABASE"):
        CONFIG.add_section("DATABASE")

    # Add keys and values to the new section
    CONFIG.set("DATABASE", "relay_database_path", "relays.db")
    
    # Update configuration file
    with open(CONFIG_PATH, 'w') as configfile:
        CONFIG.write(configfile)  
        print(f"[config.py] Added 'DATABASE' section to {CONFIG_PATH}")


# DEFAULT RELAYS
try:
    relays         = dict(CONFIG['RELAYS'])
    DEFAULT_RELAYS = list(relays.values())
except:
    DEFAULT_RELAYS = []


# TORRENT SOFTWARE
try:
    TORRENT_CLIENTS = CONFIG['TORRENT']["torrent_clients"]
    TORRENT_CLIENTS = [client.strip() for client in TORRENT_CLIENTS.split('|') if client.strip()]
except:
    TORRENT_CLIENTS = ['qbittorrent', 'transmission', 'deluge', 'fragments', 'ktorrent']


# QUERY RESULTS
QUERY_RESULTS_FILE_PATH = os.path.join(BASE_DIR, 'query_results.txt')