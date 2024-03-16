import os, signal, subprocess, argparse

username = ""
port = 000
name = "name"
keyfile = "example.priv"
origin = "origin"

DNS_SERVERS = ["proj4-dns.5700.network"]
REPLICA_SERVERS = ["proj4-repl2.5700.network"]

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

def get_p_table():
    cmd = ["ps", "aux"]
    res = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    res = res.stdout.read().decode()
    return res.split("\n")[1:]


def get_pid(name:str, table:str):
    pid = []
    for item in table:
        if name in item:
            data = item.split()
            pid.append(data[1])
    return pid

def killProcess(pid):
    try:
        pid = int(pid)
        os.kill(pid, signal.SIGKILL)
    except:
        return -1
    return 0

def killProcessList(pidList):
    for pid in pidList:
        killProcess(pid)


def stopAll():
    # ADD the program to kill here:
    pList = ["dnsserver.py"]
    table = get_p_table()
    # this kills the process list

    for item in pList:
        pids = get_pid(item, table)
        killProcessList(pids)
        
    for replica in REPLICA_SERVERS:
        stopCDN(replica)

# send stop to the server!
def stopCDN(replicaName:str):
    cmd = "pkill python3; pkill rust"
    test = "touch HelloThere.txt" 
    ssh = f"ssh -i {args.keyfile} {args.username}@{replicaName} '{test}'"
    os.system(ssh)
    
if __name__ == "__main__":
    args = parse_args()
    for replica in REPLICA_SERVERS:
        stopCDN(replica)
