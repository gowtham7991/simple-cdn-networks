#!/usr/bin/python3
import argparse
from functools import lru_cache
import logging
import socket
import time
from typing import Tuple
import threading
from queue import PriorityQueue
from dnslib import *
import requests
import json
from urllib.request import urlopen
from math import radians, cos, sin, asin, sqrt, inf
import geoip2.database


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
REPLICA_SERVERS = {
    '139.144.30.25',
    '173.255.210.124',
    '139.144.69.56',
    '185.3.95.25',
    '139.162.83.107',
    '192.46.211.228',
    '170.187.240.5',
}

UPDATE_ROUTING_TABLE_FREQUENCY = 300
PING_REPLICA_SERVERS_FREQUENCY = 100

def find_closest_replica_server(source_ip):
    DEFAULT_REPLICA_SERVER = '139.144.30.25'
    source_coordinates = find_location_coordinates(source_ip)
    return min(REPLICA_SERVERS,
               key=lambda repl: distance_between_locations(
                   source_coordinates, find_location_coordinates(repl)),
               default=DEFAULT_REPLICA_SERVER)


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
    return (c * r)


@lru_cache(maxsize=32)
def find_location_coordinates(ip):
    # url = 'https://geolocation-db.com/jsonp/' + ip
    # response = urlopen(url)
    # data = json.load(response)
    with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
        response = reader.city(ip)

    lat = float(response.location.latitude)
    lon = float(response.location.longitude)

    return (lat, lon)


def resolve(client_address: Tuple[str, int]) -> str:
    client_ip = client_address[0]

    if client_ip not in CLIENT_REPLICA_ROUTING_TABLE:
        closest_server = find_closest_replica_server(client_ip)
        CLIENT_REPLICA_ROUTING_TABLE[client_ip] = {
            'replica_server': closest_server,
            'latency': inf
        }

    return CLIENT_REPLICA_ROUTING_TABLE[client_ip]['replica_server']

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

def serve_dns(port):

    localIP = get_ip_address()
    bufferSize = 1024

    udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_sock.bind((localIP, port))
    logging.info(f"Listening on {localIP}:{port}")
    while True:
        message, address = udp_sock.recvfrom(bufferSize)
        threading.Thread(target=process_request, args=(udp_sock, message, address)).start()

def process_request(udp_sock, message, address):
    query = DNSRecord.parse(message)
    logging.debug(f"Received {query} from {address}")
    question = str(query.q).split()[0][1:-1]
    repsonse = DNSRecord(DNSHeader(id=query.header.id, qr=1, aa=0, ra=1),
                             q=DNSQuestion(question),
                             a=RR(question, rdata=A(resolve(address))))
    logging.debug(f"Sending {repsonse} to {address}")
    udp_sock.sendto(repsonse.pack(), address)


def ping_replica_servers():
    while True:
        for replica in REPLICA_SERVERS.keys():
            response = requests.post('http:/new_func/' + replica + ':25015/ping', json = " ".join(list(CLIENT_REPLICA_ROUTING_TABLE.keys())))
            print(response.json())
        time.sleep(PING_REPLICA_SERVERS_FREQUENCY)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()

    ping_thread = threading.Thread(target=ping_replica_servers)
    ping_thread.start()
    serve_dns(args.port)
