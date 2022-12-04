#!/usr/bin/env python3
import socket
import subprocess
import re
import json

port  = 21313

def sendCommand(cmd: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", port))
    s.sendall(cmd.encode())
    print(s.recv(2000))


def measurePing(address) -> float:
    scamp =subprocess.Popen(["scamper", "-I", "ping -c 1 -W3" + address], stdout=subprocess.PIPE)
    result = scamp.stdout.read().decode() 
    if matches:= re.findall("time=[0-9.]+", result):
        time = matches[0][5:]
    else:
        time = "inf"
    print(time)
    return float(time)


def measureMultiplePing(addresses):
    cmd = ["scamper","-i","-c", "ping -c 1", *addresses]
    scamp = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    result = scamp.stdout.read().decode()
    result = result.split("---\n")
    times = []
    for item in result:
        if matches := re.findall("time=([0-9.]+)", item):
            currTime=matches[0]
        else:
            currTime = "inf"
        times.append(float(currTime))
    return {client:{"rtt":rtt} for client, rtt in zip(addresses,times)}


def launch():
    list_files = subprocess.run(["scamper", "-P", str(port), "-D"])


if __name__ == "__main__":
    measureMultiplePing(["192.168.1.1", "8.8.4.4", "8.8.8.8", "8.6.54.3"])
