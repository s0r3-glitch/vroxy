from __future__ import unicode_literals
import os
import logging as log
from aiohttp import web

from app.config import config
from app.middleware import makeTokenAuthzMiddleware
from app.resolver import resolveUrl
from app.normalize import normalizeUrl, normalizeLocal
from app.exceptions import *

routes = web.RouteTableDef()
log.basicConfig(level=log.DEBUG)


@routes.view("/healthz")
class Health(web.View):
    async def get(self):
        return web.Response(status=200, text="OK")

@routes.view("/")
class YTDLProxy(web.View):
    async def head(self):
        log.debug('HEAD headers')
        log.debug(self.request.headers)
        if not self.request.query.get("url") and not self.request.query.get("u"):
            res = web.Response(status=404)
            return res
        return await self.process()

    async def get(self):
        log.debug(f'GET:Headers: {self.request.headers}')
        # handles all the logic for youtube videos
        if self.request.query.get("url") or self.request.query.get("u"):
            log.debug(f'GET:URL:Raw: {self.request.query.get("url")}')
        
            # Runs the URL through the normalizer
            url = normalizeUrl(self.request.query.get("url") or self.request.query.get("u"))
            log.debug(f"GET:Normalize:URL: {url}")

            # Processes the URL through the resolver and then returns the response
            return await self.process()

           # handles all the logic for local files     
        elif self.request.query.get("local") or self.request.query.get("l"):
            log.debug(f'GET:Local:Raw: {self.request.query.get("local")}')
            #Runs the URL through the normalizer
            url = normalizeLocal(self.request.query.get("local") or self.request.query.get("l"))
            if url == 404:
                log.debug(f"GET:Local: Yo shit aint found fam fuck off")
                res = web.Response(status=404, text="Yo shit aint found fuck off")
                return res
            log.debug(f"GET:Normalize:Local: {url}")
            #returns the file
            
            log.debug(f"GET:Local: We found yo shit fam here yous go")
            return web.FileResponse(url)
        
        # Fall back to 404 if no url or local is provided
        else:
            res = web.Response(status=404, text="Missing Url Param")
            return res
        

    async def process(self):
        log.debug('Processing request')
        url = None
        res = web.Response(status=500)
        try:
            url = await resolveUrl(self.request.query)
            res = web.Response(status=307, headers={"Location": url})
        except Error400BadRequest:
            res = web.Response(status=400)
        except Error403Forbidden:
            res = web.Response(status=403)
        except Error403Whitelist:
            res = web.Response(status=403, text="Domain not in whitelist")
        except Error404NotFound:
            res = web.Response(status=404)
        except Error408Timeout:
            res = web.Response(status=408)
        except Error410Gone:
            res = web.Response(status=410)
        except Error429TooManyRequests:
            res = web.Response(status=429)
        except Exception:
            res = web.Response(status=500)
        return res


async def strip_headers(req: web.Request, res: web.StreamResponse):
    del res.headers['Server']

app = web.Application()
if auth_tokens_config := config["server"].get("auth_tokens"):
    auth_tokens = [t.strip() for t in auth_tokens_config.split(",")]
    authz_middleware = makeTokenAuthzMiddleware(auth_tokens)
    app.middlewares.append(authz_middleware)

app.add_routes(routes)
app.on_response_prepare.append(strip_headers)
print("Starting Vroxy server.")
if os.environ.get("TMUX"):
    print("--- TMUX USAGE REMINDER ---")
    print("If the service is running in a TMUX instance, you can exit without killing the service with CTRL+B and then press D")
    print("If you run the CTRL+C command, you will kill the service making your urls return 502.")
    print(f"Remember you can restart the service by exiting the TMUX instance with CTRL+B and then D, then run 'bash {os.path.dirname(__file__)}/vroxy_reload.sh'", flush=True)
web.run_app(app, host=config["server"]["host"], port=config["server"]["port"])
