<<<<<<< HEAD
import logging
import os
import subprocess
from aiohttp import web
from aiohttp import ClientSession
import brotli
import tarfile

logging.basicConfig(level=logging.DEBUG)
app = web.Application()
routes = web.RouteTableDef()
RAM_CACHE = {}
DISK_CACHE = tarfile.open("disk.tar", "r")


async def fetch_from_origin(path):
    logging.debug(f"Fetching {path} from origin")
    async with ClientSession() as session:
        async with session.get(
                f"http://cs5700cdnorigin.ccs.neu.edu:8080/{path}") as resp:
            return await resp.text()


@routes.post("/preload")
async def preload(request):
    global RAM_CACHE
    RAM_CACHE = {
        page: brotli.compress((await fetch_from_origin(page)).encode())
        for page in await request.json()
    }
    return web.Response(status=204)


@routes.get("/grading/beacon")
async def beacon(request):
    return web.Response(text="", status=204)


@routes.get("/{path:.*}")
async def proxy(request):
    path = request.match_info["path"]
    if path in RAM_CACHE:
        response = brotli.decompress(RAM_CACHE[path]).decode()
        return web.Response(text=response, content_type="text/html")
    try:
        f = DISK_CACHE.extractfile(f"./{path}.br")
        return web.Response(text=brotli.decompress(f.read()).decode(),
                            content_type="text/html")
    except KeyError:
        response = await fetch_from_origin(path)
        return web.Response(text=response, content_type="text/html")


app.add_routes(routes)
web.run_app(app, port=25015)
=======
from aiohttp import web
from aiohttp import ClientSession
from functools import cache
import json
import subprocess
import re

app = web.Application()
routes = web.RouteTableDef()
cache = {}
FILE = "out.json"
clients = set()
rttList = {}

# TODO: Cache with expiry
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

async def fetch_from_origin(path):
    if path in cache:
        return cache[path]
    async with ClientSession() as session:
        async with session.get(f"http://cs5700cdnorigin.ccs.neu.edu:8080/{path}") as resp:
            cache[path] = await resp.text()
            return cache[path]

@routes.get("/grading/beacon")
async def beacon(request):
    return web.Response(text="", status=204)

@routes.post("/ping")
async def updateClients(request):
    global clients
    incomingClients = set(await request.json()) 
    clients |= incomingClients
    return web.Response(text="",status=200)

@routes.get("/ping")
async def ping(request):
    return web.json_response(measureMultiplePing(list(clients)))

@routes.get("/{path:.*}")
async def proxy(request):
    resp = await fetch_from_origin(request.match_info["path"])
    return web.Response(text=resp, content_type="text/html")

app.add_routes(routes)
web.run_app(app, port=25015)
>>>>>>> 98c138b (added untested server response for pinging a host)
