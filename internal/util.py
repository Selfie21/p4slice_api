import ipaddress

def ip2int(ip):
    return int(ipaddress.ip_address(ip))

def int2ip(ip):
    return ipaddress.ip_address(ip)