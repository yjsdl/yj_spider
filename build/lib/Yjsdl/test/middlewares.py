#!/usr/bin/env python

from Yjsdl import Middleware, Request
from Yjsdl.utils import get_logger

middleware = Middleware()


@middleware.request
async def request_ua(spider_ins, request: Request):
    """request using proxy example"""

    logger = get_logger(name='change_ua')
    # HTTP proxy
    # request.aiohttp_kwargs.update({"proxy": "http://0.0.0.0:1087"})

    # SOCKS5 proxy using aiohttp_socks
    # Check docs in https://pypi.org/project/aiohttp-socks/
    # from aiohttp import ClientSession
    # from aiohttp_socks import ProxyConnector
    # connector = ProxyConnector.from_url('socks5://127.0.0.1:9999')
    # request.request_session = ClientSession(connector=connector)
    # request.close_request_session = True
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    logger.info('更新ua-------------------------')
    request.headers.update({"User-Agent": ua})
