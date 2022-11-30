#!/usr/bin/python3
"""Strategy: Always origin"""
import argparse
import logging
import socket
from typing import Tuple

from dnslib import *


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


def resolve(client_address: Tuple[str, int]) -> str:
    return ORIGIN_IP


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
        query = DNSRecord.parse(message)
        logging.debug(f"Received {query} from {address}")
        question = str(query.q).split()[0][1:-1]
        repsonse = DNSRecord(DNSHeader(id=query.header.id, qr=1, aa=0, ra=1),
                             q=DNSQuestion(question),
                             a=RR(question, rdata=A(resolve(address))))
        logging.debug(f"Sending {repsonse} to {address}")
        udp_sock.sendto(repsonse.pack(), address)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    serve_dns(args.port)