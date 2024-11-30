import ipaddress
from models import BaseSlice

def ip2int(ip):
    return int(ipaddress.ip_address(ip))

def int2ip(ip):
    return ipaddress.ip_address(ip)

def insert_into_database(database: dict, slice: BaseSlice):
    free_slot = 0
    for index, entry in enumerate(database):
        if not entry:
            free_slot = index
            database[free_slot] = slice

    if len(database) == 0:
        database[free_slot] = slice 
    return free_slot
