from functools import lru_cache
import logging
import re
import subprocess
import time
from aiohttp import web
from aiohttp import ClientSession
import brotli
import tarfile
import time

logging.basicConfig(level=logging.DEBUG)
app = web.Application()
routes = web.RouteTableDef()
RAM_CACHE = {}
DISK_CACHE = tarfile.open("disk.tar", "r")
CLIENTS = set()

PING_CACHE = {}
PING_CACHE_EXPIRY = 100  # seconds

# uses scamper to ping multiple clients and parses the response
def measureMultiplePing(addresses):
    if len(addresses) == 0: return {}
    if addresses in PING_CACHE and PING_CACHE[addresses][
            'expiry'] >= time.time():
        return PING_CACHE[addresses]['result']
    PING_CACHE.clear()
    cmd = ["scamper", "-i", "-c", "ping -c 1", *addresses]
    scamp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    result = scamp.stdout.read().decode()
    result = result.split("---\n")
    times = []
    for item in result:
        if matches := re.findall("time=([0-9.]+)", item):
            currTime = matches[0]
        else:
            currTime = "inf"
        times.append(float(currTime))
    result = {client: {"rtt": rtt} for client, rtt in zip(addresses, times)}
    PING_CACHE[addresses] = {
        'expiry': time.time() + PING_CACHE_EXPIRY,
        'result': result
    }
    return result

# fetches content from the origin
async def fetch_from_origin(path):
    logging.debug(f"Fetching {path} from origin")
    async with ClientSession() as session:
        async with session.get(
                f"http://cs5700cdnorigin.ccs.neu.edu:8080/{path}") as resp:
            return await resp.text()

# responds to the ping call for the clients with the latencies
@routes.post("/ping")
async def updateClients(request):
    global CLIENTS
    incomingClients = set(await request.json())
    CLIENTS |= incomingClients
    return web.Response(status=204)


@routes.get("/ping")
async def ping(request):
    return web.json_response(measureMultiplePing(tuple(sorted(CLIENTS))))

# preloads the cache with the compressed content from the origin 
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
