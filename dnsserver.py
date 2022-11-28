"""Strategy: Always origin"""
import argparse
import logging
import socket
from typing import Tuple
import threading
from queue import PriorityQueue
from dnslib import *
import requests
import json
from urllib.request import urlopen
from math import radians, cos, sin, asin, sqrt, inf

def get_ip_address():
    """Get local IP address.

    Returns
    -------
    IPv4Address
        Local IP address
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


ORIGIN = "cs5700cdnorigin.ccs.neu.edu"
ORIGIN_IP = socket.gethostbyname(ORIGIN)
CLIENT_REPLICA_ROUTING_TABLE = {}
REPLICA_SERVERS = {'139.144.30.25' : 'proj4-repl1.5700.network'}
UPDATE_ROUTING_TABLE_FREQUENCY = 300
PING_REPLICA_SERVERS_FREQUENCY = 100

def find_closest_replica_server(source_ip):
    source_coordinates = find_location_coordinates(source_ip)
    
    min_dist = inf
    closest_server = REPLICA_SERVERS.keys()[0]

    for server in REPLICA_SERVERS.keys():
        server_coordinates = find_location_coordinates(server)
        dist = distance_between_locations(server_coordinates, source_coordinates)
        if dist < min_dist:
            closest_server = server

    return closest_server

def distance_between_locations(loc1, loc2):
     
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(loc1[0])
    lon2 = radians(loc1[1])
    lat1 = radians(loc2[0])
    lat2 = radians(loc2[1])
      
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result
    return(c * r)

def find_location_coordinates(ip):
    url = 'http://ipinfo.io/' + ip + '/json'
    response = urlopen(url)
    data = json.load(response)
    print(data)
    lat = float(data['loc'].split(",")[0])
    lon = float(data['loc'].split(",")[1])
    
    return (lat, lon)

def resolve(client_address: Tuple[str, int])-> Tuple[str, str]:
    client_ip = client_address[0]
    
    if client_ip not in CLIENT_REPLICA_ROUTING_TABLE:
        closest_server = find_closest_replica_server(client_ip)
        CLIENT_REPLICA_ROUTING_TABLE[client_ip] = {'replica_server' : closest_server, 'latency': inf}

    return (REPLICA_SERVERS[ CLIENT_REPLICA_ROUTING_TABLE[client_ip]['replica_server']], CLIENT_REPLICA_ROUTING_TABLE[client_ip]['replica_server'])

def parse_args():
    parser = argparse.ArgumentParser(description='DNS Server')
    parser.add_argument("-p",
                        "--port",
                        required=True,
                        type=int,
                        help='Port to listen on')
    parser.add_argument("-n",
                        "--name",
                        required=True,
                        help='CDN specific name')
    return parser.parse_args()

def serve_dns(port, server_domain):

    localIP = get_ip_address()
    bufferSize = 1024

    udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_sock.bind((localIP, port))
    logging.info(f"Listening on {localIP}:{port}")

    while True:
        message, address = udp_sock.recvfrom(bufferSize)
        query = DNSRecord.parse(message)
        logging.debug(f"Received {query} from {address}")
        server_domain, server_ip = resolve(address)
        repsonse = DNSRecord(DNSHeader(id=query.header.id, qr=0, aa=1,
                                          ra=1),
                                a=RR(server_domain,
                                     rdata=A(server_ip)))
        logging.debug(f"Sending {repsonse} to {address}")
        udp_sock.sendto(repsonse.pack(), address)

def update_client_replica_routing():
    for replica in REPLICA_SERVERS.keys():
        response = requests.get('http://' + replica + '/ping')
        data = response.json()

        for client in data:
            if data[client] < CLIENT_REPLICA_ROUTING_TABLE[client]['latency']:
                CLIENT_REPLICA_ROUTING_TABLE[client]['replica_server'] = replica
                CLIENT_REPLICA_ROUTING_TABLE[client]['latency'] = data[client] 

def ping_replica_servers():
    for replica in REPLICA_SERVERS.keys():
        body = {'clients' : list(CLIENT_REPLICA_ROUTING_TABLE.keys())}
        requests.post('http://' + replica + '/ping', json = body)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    update_client_replica_routing()
    ping_replica_servers()
    threading.Timer(UPDATE_ROUTING_TABLE_FREQUENCY, update_client_replica_routing).start()
    threading.Timer(PING_REPLICA_SERVERS_FREQUENCY, ping_replica_servers).start()
    serve_dns(args.port, args.name)