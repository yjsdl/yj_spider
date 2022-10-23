#!/usr/bin/env python

import asyncio
import weakref

from asyncio.locks import Semaphore
from inspect import iscoroutinefunction
from types import AsyncGeneratorType
from typing import Coroutine, Optional, Tuple

import aiohttp
import async_timeout

from Yjsdl.exceptions import InvalidRequestMethod
from Yjsdl.utils import get_logger

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class Request:
    """
    Request class for each request
    """

    name = "Request"

    # Default config
    REQUEST_CONFIG = {
        "RETRIES": 3,
        "DELAY": 0,
        "RETRY_DELAY": 0,
        # 超时时间
        "TIMEOUT": 10,
        # 设置重试的参数
        "RETRY_FUNC": Coroutine,
        # 对响应数据修改
        "VALID": Coroutine,
    }

    METHOD = ["GET", "POST"]

    def __init__(
            self,
            url: str,
            method: str = "GET",
            params=None,
            data=None,
            cookies=None,
            *,
            callback=None,
            encoding: Optional[str] = None,
            headers: dict = None,
            meta: dict = None,
            request_config: dict = None,
            priority: Optional[int] = 1,
            **aiohttp_kwargs,
    ):
        """
        Initialization parameters
        :param url: Target url
        :param method: HTTP method
        :param callback: Callback func
        :param encoding: Html encoding
        :param headers: Request headers
        :param meta: Send the data to callback func
        :param request_config: Manage the target request
        :param request_session: aiohttp.ClientSession
        :param aiohttp_kwargs:
        """
        self.url = url
        self.method = method.upper()

        if self.method not in self.METHOD:
            raise InvalidRequestMethod(f"{self.method} method is not supported")

        self.params = params or {}
        self.cookie = cookies or {}
        self.data = data or {}
        self.callback = callback
        self.encoding = encoding
        self.headers = headers or {}
        self.meta = meta or {}
        self.priority = priority
        self.request_config = (
            self.REQUEST_CONFIG if request_config is None else request_config
        )
        self.ssl = aiohttp_kwargs.pop("ssl", False)
        self.aiohttp_kwargs = aiohttp_kwargs

        self.close_request_session = False
        self.logger = get_logger(name=self.name)
        self.retry_times = self.request_config.get("RETRIES", 3)

    def __lt__(self, other):
        # 自定义的类定义了__lt__, 可以比较大小
        # 解决 TypeError: '<' not supported between instances of 'Request' and 'Request'
        return self.priority < other.priority

    def __repr__(self):
        return f"<{self.method} {self.url}>"
