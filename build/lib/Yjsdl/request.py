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
from Yjsdl.response import Response
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
            request_session=None,
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

        self.params = params or ''
        self.cookie = cookies or {}
        self.data = data or {}
        self.callback = callback
        self.encoding = encoding
        self.headers = headers or {}
        self.meta = meta or {}
        self.request_session = request_session
        self.request_config = (
            self.REQUEST_CONFIG if request_config is None else request_config
        )
        self.ssl = aiohttp_kwargs.pop("ssl", False)
        self.aiohttp_kwargs = aiohttp_kwargs

        self.close_request_session = False
        self.logger = get_logger(name=self.name)
        self.retry_times = self.request_config.get("RETRIES", 3)

    @property
    def current_request_session(self):
        if self.request_session is None:
            self.request_session = aiohttp.ClientSession()
            self.close_request_session = True
        return self.request_session

    async def fetch(self, delay=True) -> Response:
        """Fetch all the information by using aiohttp"""
        if delay and self.request_config.get("DELAY", 0) > 0:
            await asyncio.sleep(self.request_config["DELAY"])

        timeout = self.request_config.get("TIMEOUT", 10)
        try:
            async with async_timeout.timeout(timeout):
                resp = await self._make_request()
            try:
                resp_encoding = resp.get_encoding()
            except:
                resp_encoding = self.encoding

            response = Response(
                url=str(resp.url),
                method=resp.method,
                encoding=resp_encoding,
                meta=self.meta,
                cookies=resp.cookies,
                history=resp.history,
                headers=resp.headers,
                status=resp.status,
                aws_json=resp.json,
                aws_text=resp.text,
                aws_read=resp.read,
            )
            # Retry middleware
            # response is coroutine，修改响应数据
            aws_valid_response = self.request_config.get("VALID")
            if aws_valid_response and iscoroutinefunction(aws_valid_response):
                response = await aws_valid_response(response)
            if response.ok:
                return response
            else:
                return await self._retry(
                    error_msg=f"Request url failed with status {response.status}!"
                )
        except asyncio.TimeoutError:
            return await self._retry(error_msg="timeout")
        except Exception as e:
            return await self._retry(error_msg=e)
        finally:
            # Close client session
            if self.close_request_session:
                await self._close_request()

    # 进入request的第一个协程
    async def fetch_callback(
            self, sem: Semaphore
    ) -> Tuple[AsyncGeneratorType, Response]:
        """
        Request the target url and then call the callback function
        :param sem: Semaphore
        :return: Tuple[AsyncGeneratorType, Response]
        """
        try:
            async with sem:
                response = await self.fetch()
        except Exception as e:
            response = None
            self.logger.error(f"<Error: {self.url} {e}>")

        if self.callback is not None:
            if iscoroutinefunction(self.callback):
                callback_result = await self.callback(response)
            else:
                callback_result = self.callback(response)
        else:
            callback_result = None
        return callback_result, response

    async def _close_request(self):
        """
        Close the aiohttp session
        :return:
        """
        await self.request_session.close()

    async def _make_request(self):
        """Make a request by using aiohttp"""
        self.logger.info(f"<{self.method}: {self.url}>")
        if self.method == "GET":
            request_func = self.current_request_session.get(
                self.url, headers=self.headers, ssl=self.ssl, **self.aiohttp_kwargs
            )
        else:
            request_func = self.current_request_session.post(
                self.url, headers=self.headers, params=self.params, data=self.data, ssl=self.ssl, **self.aiohttp_kwargs
            )
        resp = await request_func
        return resp

    async def _retry(self, error_msg):
        """Manage request"""
        if self.retry_times > 0:
            # Sleep to give server a chance to process/cache prior request
            if self.request_config.get("RETRY_DELAY", 0) > 0:
                await asyncio.sleep(self.request_config["RETRY_DELAY"])

            retry_times = self.request_config.get("RETRIES", 3) - self.retry_times + 1
            self.logger.exception(
                f"<Retry url: {self.url}>, Retry times: {retry_times}, Retry message: {error_msg}>"
            )
            self.retry_times -= 1

            # 加载重试时的配置
            retry_func = self.request_config.get("RETRY_FUNC")
            if retry_func and iscoroutinefunction(retry_func):
                request_ins = await retry_func(weakref.proxy(self))
                if isinstance(request_ins, Request):
                    return await request_ins.fetch(delay=False)
            return await self.fetch(delay=False)
        else:
            response = Response(
                url=self.url,
                method=self.method,
                meta=self.meta,
                cookies={},
                history=(),
                headers=None,
            )

            return response

    def __repr__(self):
        return f"<{self.method} {self.url}>"
