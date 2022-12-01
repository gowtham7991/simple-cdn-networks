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