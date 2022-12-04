#!/usr/bin/python3
import argparse
import logging
import os
from typing import List

username = ""
port = 000
name = "name"
keyfile = "example.priv"
origin = "origin"

DNS_SERVERS = ["proj4-dns.5700.network"]
REPLICA_SERVERS = ["proj4-repl1.5700.network"]

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy CDN')
    parser.add_argument("-p",
                        "--port",
                        metavar=port,
                        required=False,
                        help='Port to listen on')
    parser.add_argument("-o", "--origin",
                        metavar=origin,
                        required=False, 
                        help='Origin server')
    parser.add_argument("-n",
                        "--name",
                        metavar=name,
                        required=False,
                        help='CDN specific name')
    parser.add_argument("-u",
                        "--username",
                        metavar=username,
                        required=True,
                        help='Username used for login')
    parser.add_argument("-i",
                        "--keyfile",
                        metavar=keyfile,
                        required=True,
                        help='Keyfile used for login')

    return parser.parse_args()

#send deploy command
def deployCommand(dns_server: List[str], replica_servers: List[str]):
    dns_cmd = f"./httpserver -o {origin}"
    for server in dns_server:
        cmd = f"ssh -i {args.keyfile} {args.username}@{server} '{dns_cmd}'"
        logging.debug(f"Running command {cmd}")
        os.system(cmd)
        logging.info(f"Deployed DNS server on {server}")

def compileRustServer(replicaName):
    cmd  = "cargo build --release && upx --best --lzma target/release/server"
    ssh = f"ssh -i {keyfile} {username}@{replicaName} '{cmd}'"
    os.system(ssh)


#copy files to replicas
def copyToReplica(replicaName):
    # copy server
    scpCmd = f"scp -i {keyfile} /target/release/server {username}@{replicaName}:/home/dkgp/target/release/server"
    os.system(scpCmd)
    # copy data cache into replica
    scpCmd = f"scp -i {keyfile}  -r disk/ {username}@{replicaName}:disk/"
    os.system(scpCmd)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    for replicaName in REPLICA_SERVERS:
        copyToReplica(replicaName)