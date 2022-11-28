#!/usr/bin/python3
import argparse
import logging
import os
from typing import List


def parse_args():
    parser = argparse.ArgumentParser(description='Deploy CDN')
    parser.add_argument("-p",
                        "--port",
                        required=True,
                        help='Port to listen on')
    parser.add_argument("-o", "--origin", required=True, help='Origin server')
    parser.add_argument("-n",
                        "--name",
                        required=True,
                        help='CDN specific name')
    parser.add_argument("-u",
                        "--username",
                        required=True,
                        help='Username used for login')
    parser.add_argument("-i",
                        "--keyfile",
                        required=True,
                        help='Keyfile used for login')

    return parser.parse_args()


def deploy(dns_server: List[str], replica_servers: List[str]):
    dns_cmd = f"date"
    for server in dns_server:
        cmd = f"ssh -i {args.keyfile} {args.username}@{server} '{dns_cmd}'"
        logging.debug(f"Running command {cmd}")
        os.system(cmd)
        logging.info(f"Deployed DNS server on {server}")


if __name__ == "__main__":
    DNS_SERVERS = ["proj4-dns.5700.network"]
    REPLICA_SERVERS = ["proj4-repl1.5700.network"]

    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    deploy(DNS_SERVERS, REPLICA_SERVERS)