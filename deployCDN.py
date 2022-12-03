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
                        required=True,
                        help='Port to listen on')
    parser.add_argument("-o", "--origin",
                        metavar=origin,
                        required=True, 
                        help='Origin server')
    parser.add_argument("-n",
                        "--name",
                        metavar=name,
                        required=True,
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

#copy files to replicas
def copyToReplica(replicaName, username, port):
    # add the files as needed 
    scpCmd = "scp -i sshKey -p " + port + "localhost:/home/dkgp/httpserver.py " + username + "@" + replicaName + ":/home/dkgp/test/"
    os.system(scpCmd)
    
    scpCmd = "scp -i sshKey -p " + port + "localhost:/home/dkgp/disk.tar " + username + "@" + replicaName + ":/home/dkgp/test/"
    os.system(scpCmd)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    for replica in REPLICA_SERVERS:
        copyToReplica(replica, username, port)
    deployCommand(DNS_SERVERS, REPLICA_SERVERS)
