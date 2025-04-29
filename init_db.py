#!/usr/bin/env python
import configparser
import unicodedata
import requests
import sqlite3
import json
import os

from config import CONFIG, BASE_DIR, DATABASE_PATH


### --- IF USING THIS VERSION, REMOVE `TYPE` FROM QUERY OUTPUT --- ###



## -----------  RETRIEVE DATA FROM MULLVAD ----------- ##

RELAYS_URL = "https://api.mullvad.net/www/relays/all/"

# # Ensure database is reset (optional)
# if os.path.exists(DATABASE_PATH):
#     os.remove(DATABASE_PATH)

# Get the server list data
response = requests.get(RELAYS_URL)

try:
    response = requests.get(RELAYS_URL, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching relays data: {e}")
    exit(1)


# Convert to json and remove openvpn and bridge relays from data
data = response.json()
data = [relay for relay in data if relay['type'] == 'wireguard']


## -----------  CREATE / UPDATE SQLITE DATABASE TABLES  ----------- ##

conn   = sqlite3.connect(DATABASE_PATH)  
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS relays (
    hostname TEXT PRIMARY KEY,
    country_code TEXT,
    country_name TEXT,
    city_code TEXT,
    city_name TEXT,
    fqdn TEXT,
    active INTEGER CHECK(active IN (0, 1)),
    owned INTEGER CHECK(owned IN (0, 1)),
    provider TEXT,
    ipv4_addr_in TEXT,
    ipv6_addr_in TEXT,
    network_port_speed INTEGER,
    stboot INTEGER CHECK(stboot IN (0, 1)),
    pubkey TEXT,
    multihop_port INTEGER,
    socks_name TEXT,
    socks_port INTEGER,
    daita INTEGER CHECK(daita IN (0, 1)),
    type TEXT CHECK(type IN ('wireguard')),
    status_messages TEXT
)
''')

## -----------  PREPARE DATA FOR DATABASE ----------- ##

def _convert_message_to_str(status_message):
    try:
        return f"[{status_message[0]['timestamp']}] {status_message[0]['message']}"
    except (IndexError, KeyError, TypeError):
        return ""


def _normalize_text(text):
    '''
    Converts accented city and country names like Malmö to Malmo.
    '''
    return ''.join(
        # Normal form D (NFD) translates each character into its decomposed form
        c for c in unicodedata.normalize('NFD', text) 
        if unicodedata.category(c) != 'Mn' # 'Mn' is “Mark (ie accent marks), nonspacing”
    )

relay_data = [
    {
        "hostname"           : relay["hostname"],
        "country_code"       : relay["country_code"],
        "country_name"       : relay["country_name"],
        "city_code"          : relay["city_code"],
        "city_name"          : _normalize_text(relay["city_name"]),
        "fqdn"               : relay["fqdn"],
        "active"             : relay["active"],
        "owned"              : relay["owned"],
        "provider"           : relay["provider"],
        "ipv4_addr_in"       : relay["ipv4_addr_in"],
        "ipv6_addr_in"       : relay["ipv6_addr_in"],
        "network_port_speed" : relay["network_port_speed"],
        "stboot"             : relay["stboot"],
        "pubkey"             : relay["pubkey"],
        "multihop_port"      : relay["multihop_port"],
        "socks_name"         : relay["socks_name"],
        "socks_port"         : relay["socks_port"],
        "daita"              : relay["daita"],
        "type"               : relay["type"],
        "status_messages"    : _convert_message_to_str(relay["status_messages"])
    }
    for relay in data
]

## -----------  INSERT DATA INTO DATABASE  ----------- ##

cursor.executemany("""
    INSERT OR REPLACE INTO relays (
        hostname,
        country_code,
        country_name,
        city_code,
        city_name,
        fqdn,
        active,
        owned,
        provider,
        ipv4_addr_in,
        ipv6_addr_in,
        network_port_speed,
        stboot,
        pubkey,
        multihop_port,
        socks_name,
        socks_port,
        daita,
        type,
        status_messages
    ) VALUES (
        :hostname,
        :country_code,
        :country_name,
        :city_code,
        :city_name,
        :fqdn,
        :active,
        :owned,
        :provider,
        :ipv4_addr_in,
        :ipv6_addr_in,
        :network_port_speed,
        :stboot,
        :pubkey,
        :multihop_port,
        :socks_name,
        :socks_port,
        :daita,
        :type,
        :status_messages
    )
""", relay_data)

## -----------  COMMIT & CLOSE ----------- ##
conn.commit()
conn.close()