import os, signal, subprocess, argparse
import logging

username = ""
port = 000
name = "name"
keyfile = "example.priv"
origin = "origin"

DNS_SERVERS = ["proj4-dns.5700.network"]
REPLICA_SERVERS = ["proj4-repl1.5700.network"]

def parse_args():
    parser = argparse.ArgumentParser(description='run CDN')
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


def runCDN(replicaName):
    cmd = f"./target/release/server"
    ssh = f"ssh -i {keyfile} {username}@{replicaName} '{cmd}'"
    os.system(ssh)
    


if __name__ == "__main__":
    args = parse_args()
    for replica in REPLICA_SERVERS:
        runCDN(replica)