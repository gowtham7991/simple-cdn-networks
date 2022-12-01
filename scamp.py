#!/usr/bin/env python3

import socket
import subprocess
import re
import argparse

port  = 21313

def sendCommand(cmd: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", port))
    s.sendall(cmd.encode())
    print(s.recv(2000))


def measurePing(address) -> float:
    scamp =subprocess.Popen(["scamper", "-I", "ping -c 1 " + address], stdout=subprocess.PIPE)
    result = scamp.stdout.read().decode()
    try: 
        time = re.findall("time=[0-9.]+", result)[0][5:]
    except:
        time = "0"
    print(time)
    return float(time)

def launch():
    list_files = subprocess.run(["scamper", "-P", str(port), "-D"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='measures ping time')
    parser.add_argument('address', metavar='ip', type=str, help='enter the ip in string form')
    args = parser.parse_args()
    address = args.address
    measurePing(address)
