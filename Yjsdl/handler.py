# -*- coding: utf-8 -*-
# @Time    : 2022/8/22 0:23
# @Author  : Liuyijie
# @File    : handler.py
import asyncio
import aiohttp
from inspect import iscoroutinefunction
from Yjsdl.utils import get_logger
from Yjsdl import Request, Response


class DownloadHandler:
    name = "DownloadHandler"

    def __init__(self):
        self.logger = get_logger(name=self.name)

    async def fetch(self, request, delay=True) -> Response:
        """
        requests and deal response
        :param request:
        :param delay:
        :return: response or requests
        """
        request_config = request.request_config
        if delay and request_config.get("DELAY", 0) > 0:
            await asyncio.sleep(request_config["DELAY"])

        try:
            content, resp = await self._make_request(request)

            response = Response(
                url=str(resp.url),
                method=resp.method,
                encoding=resp.get_encoding(),
                meta=request.meta,
                cookies=resp.cookies,
                history=resp.history,
                headers=resp.headers,
                status=resp.status,
                content=content
            )
            # 处理响应数据
            aws_valid_response = request.request_config.get("VALID")
            if aws_valid_response and iscoroutinefunction(aws_valid_response):
                response = await aws_valid_response(response)
            if response.ok:
                return response
            else:
                return await self._retry(request,
                                         error_msg=f"Request url failed with status {response.status}!"
                                         )
        except asyncio.TimeoutError:
            return await self._retry(request, error_msg="timeout", status=300)
        except aiohttp.ClientHttpProxyError as ProxyError:
            return await self._retry(request, error_msg=ProxyError, status=401)
        except aiohttp.ClientConnectorError as CCError:
            return await self._retry(request, error_msg=CCError, status=402)
        except Exception as e:
            return await self._retry(request, error_msg=e, status=777)

    async def _make_request(self, request):
        """
        request
        :param request:
        :return:
        """
        self.logger.info(f"<{request.method}: {request.url}>")
        aiohttp_kwargs = {}
        aiohttp_kwargs.setdefault('headers', request.headers)
        aiohttp_kwargs.setdefault('params', request.params)
        aiohttp_kwargs.setdefault('data', request.data)
        aiohttp_kwargs.setdefault('ssl', request.ssl)
        aiohttp_kwargs.setdefault('timeout',
                                  aiohttp.ClientTimeout(total=request.request_config.get('TIMEOUT', 10)))

        aiohttp_kwargs.update(request.aiohttp_kwargs)

        async with aiohttp.ClientSession(cookies=request.cookie, connector=aiohttp.TCPConnector(ssl=False),
                                         trust_env=True) as session:
            request_func = await session.request(method=request.method, url=request.url, **aiohttp_kwargs)
            content = await request_func.read()
        return content, request_func

    async def _retry(self, request, error_msg, status: int = None):
        """
        request retry
        :param request:
        :param error_msg:
        :return:
        """
        if request.retry_times > 0:

            await asyncio.sleep(request.request_config.get("RETRY_DELAY", 0))
            retry_times = request.request_config.get("RETRIES", 3) - request.retry_times + 1
            self.logger.exception(
                f"<Retry url: {request.url}>, Retry times: {retry_times}, Retry message: {error_msg}>"
            )
            request.retry_times -= 1

            # 加载重试时的配置
            retry_func = request.request_config.get("RETRY_FUNC")
            if retry_func and iscoroutinefunction(retry_func):
                request_ins = await retry_func(request)
                if isinstance(request_ins, Request):
                    return request_ins
            return request
        else:
            response = Response(
                url=request.url,
                status=status,
                method=request.method,
                meta=request.meta,
                cookies={},
                history=(),
                headers=None,
            )

            return response
