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
    for page in await request.json():
        body = await fetch_from_origin(page)
        RAM_CACHE[page] = brotli.compress(body.encode())
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
        f = DISK_CACHE.extractfile(path)
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
import scamp

app = web.Application()
routes = web.RouteTableDef()
cache = {}


async def fetch_from_origin(path):
    if path in cache:
        return cache[path]
    async with ClientSession() as session:
        async with session.get(
                f"http://cs5700cdnorigin.ccs.neu.edu:8080/{path}") as resp:
            cache[path] = await resp.text()
            return cache[path]


@routes.get("/grading/beacon")
async def beacon(request):
    return web.Response(text="", status=204)


@routes.get("/{path:.*}")
async def proxy(request):
    resp = await fetch_from_origin(request.match_info["path"])
    return web.Response(text=resp, content_type="text/html")

@routes.get("/ping?client=*")
async def ping(request):
    time = await scamp.measurePing(request.match_info["path"][12:])
    return web.Response(text=time, content_type="text/html")

app.add_routes(routes)
web.run_app(app, port=25015)
>>>>>>> 98c138b (added untested server response for pinging a host)
