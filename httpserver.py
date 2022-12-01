import logging
from aiohttp import web
from aiohttp import ClientSession
import brotli
import py7zr

logging.basicConfig(level=logging.DEBUG)
app = web.Application()
routes = web.RouteTableDef()
RAM_CACHE = {}
DISK_CACHE = py7zr.SevenZipFile("disk.7z", mode="r")


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
    elif path in DISK_CACHE.getnames():
        response = DISK_CACHE.read(path)[path].read().decode()
        DISK_CACHE.reset()
    else:
        response = await fetch_from_origin(path)
    return web.Response(text=response, content_type="text/html")


app.add_routes(routes)
web.run_app(app, port=25015)