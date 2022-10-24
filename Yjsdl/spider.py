# -*- coding: utf-8 -*-
# @Time    : 2022/10/22 17:31
# @Author  : Liuyijie
# @File    : spider.py

import asyncio
import sys
import typing
import weakref

from datetime import datetime
from functools import reduce
from inspect import isawaitable
from signal import SIGINT, SIGTERM
from typing import AsyncGenerator, Generator, Coroutine

from Yjsdl.exceptions import (
    InvalidCallbackResult,
    NothingMatchedError,
    NotImplementedParseError,
    SpiderHookError,
)
from Yjsdl.item import Item
from Yjsdl import field
from Yjsdl.middleware import Middleware
from Yjsdl.request import Request
from Yjsdl.response import Response
from Yjsdl.utils import get_logger
from Yjsdl.handler import DownloadHandler
from Yjsdl.utils.UserAgent import request_ua

if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.version_info >= (3, 9):
    async_all_tasks = asyncio.all_tasks
    async_current_task = asyncio.current_task
else:
    async_all_tasks = asyncio.Task.all_tasks
    async_current_task = asyncio.tasks.Task.current_task
try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class SpiderHook:
    """
    SpiderHook is used for extend spider
    """

    callback_result_map: dict = {}

    async def _run_spider_hook(self, hook_func):
        """
        Run hook before/after spider start crawling
        :param hook_func: aws function
        :return:
        """
        if callable(hook_func):
            try:
                aws_hook_func = hook_func(weakref.proxy(self))
                if isawaitable(aws_hook_func):
                    await aws_hook_func
            except Exception as e:
                raise SpiderHookError(f"<Hook {hook_func.__name__}: {e}")

    async def process_failed_response(self, request, response):
        """
        Corresponding processing for the failed response
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_succeed_response(self, request, response):
        """
        Corresponding processing for the succeed response
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_item(self, item):
        """
        Corresponding processing for the Item type
        :param item: Item
        :return:
        """
        pass

    async def process_callback_result(self, callback_result):
        """
        Corresponding processing for the invalid callback result
        :param callback_result: Custom instance
        :return:
        """
        callback_result_name = type(callback_result).__name__
        process_func_name = self.callback_result_map.get(callback_result_name, "")
        process_func = getattr(self, process_func_name, None)
        if process_func is not None:
            await process_func(callback_result)
        else:
            raise InvalidCallbackResult(
                f"<Parse invalid callback result type: {callback_result_name}>"
            )


class Spider(SpiderHook):
    """
    Spider is used for control requests better
    """

    name = "Yjsdl"
    # 请求配置
    request_config = {
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

    start_urls: list = []

    aiohttp_kwargs: dict = {}

    failed_counts: int = 0
    success_counts: int = 0

    wait_time: int = 3
    # 并发
    concurrency: int = 3

    def __init__(
            self,
            middleware: typing.Union[typing.Iterable, Middleware] = None,
            loop=None,
            is_async_start: bool = False,
            cancel_tasks: bool = True,
            **spider_kwargs,
    ):
        """
        Init spider object.
        :param middleware: a list of or a single Middleware
        :param loop: asyncio event llo
        :param is_async_start: start spider by using async
        :param spider_kwargs
        """

        if not self.start_urls and not isinstance(self.start_requests(), AsyncGenerator):
            raise ValueError(
                "Your subject should have start_urls or async function example: start_urls = ['www.baidu.com'] ")

        self.loop = loop
        asyncio.set_event_loop(self.loop)

        self.callback_result_map = self.callback_result_map or {}

        self.request_config = self.request_config or {}

        self.aiohttp_kwargs = self.aiohttp_kwargs or {}
        self.spider_kwargs = spider_kwargs
        self.request_config = self.request_config or {}

        self.cancel_tasks = cancel_tasks
        self.is_async_start = is_async_start

        # set logger
        self.logger = get_logger(name=self.name)

        # customize middleware
        if isinstance(middleware, list):
            self.middleware = reduce(lambda x, y: x + y, middleware)
        else:
            self.middleware = middleware or Middleware()

        self.request_queue = asyncio.PriorityQueue()

    async def _process_async_callback(
            self, callback_result, response: Response = None
    ):
        try:
            if isinstance(callback_result, AsyncGenerator):
                async for result in callback_result:
                    if isinstance(result, Request):
                        self.request_queue.put_nowait(result)
                    elif isinstance(result, Item):
                        # Process target item
                        await self._process_item(result)
                    else:
                        await self.process_callback_result(callback_result=result)
            elif isinstance(callback_result, Generator):
                for result in callback_result:
                    await result
            elif isinstance(callback_result, Coroutine):
                await callback_result
            else:
                pass

        except NothingMatchedError as e:
            error_info = f"<Field: {str(e).lower()}" + f", error url: {response.url}>"
            self.logger.exception(error_info)
        except Exception as e:
            self.logger.exception(e)

    @staticmethod
    async def _process_item(item):
        func = item.__class__.name
        if func == "CsvFile":
            await field.CsvFile().process_item(item)

    async def _process_response(self, request: Request, response: Response):
        """
        cretain
        :param request:
        :param response:
        :return:
        """
        if response:
            if isinstance(response, Response):
                # Process succeed response
                self.success_counts += 1
                await self.process_succeed_response(request, response)
            else:
                self.failed_counts += 1
                await self.process_failed_response(request, response)

    async def process_succeed_response(self, request, response):

        if request.callback:
            callback = request.callback
            callback_result = callback(response)
            await self._process_async_callback(
                callback_result, response
            )

    async def process_failed_response(self, request: Request, response: Response):
        """
        deal fail request
        :param request:
        :param response:
        :return:
        """
        if isinstance(response, Request):
            self.request_queue.put_nowait(response)

    async def _run_request_middleware(self, request: Request):
        if self.middleware.request_middleware:
            for middleware in self.middleware.request_middleware:
                if callable(middleware):
                    try:
                        aws_middleware_func = middleware(self, request)
                        if isawaitable(aws_middleware_func):
                            await aws_middleware_func
                        else:
                            self.logger.error(
                                f"<Middleware {middleware.__name__}: must be a coroutine function"
                            )
                    except Exception as e:
                        self.logger.exception(f"<Middleware {middleware.__name__}: {e}")

    async def _run_response_middleware(self, request: Request, response: Response):
        if self.middleware.response_middleware:
            for middleware in self.middleware.response_middleware:
                if callable(middleware):
                    try:
                        aws_middleware_func = middleware(self, request, response)
                        if isawaitable(aws_middleware_func):
                            await aws_middleware_func
                        else:
                            self.logger.error(
                                f"<Middleware {middleware.__name__}: must be a coroutine function"
                            )
                    except Exception as e:
                        self.logger.exception(f"<Middleware {middleware.__name__}: {e}")

    async def _start(self, after_start=None, before_stop=None):
        self.logger.info("Spider started!")
        start_time = datetime.now()

        # # Add signal
        # for signal in (SIGINT, SIGTERM):
        #     try:
        #         self.loop.add_signal_handler(
        #             signal, lambda: asyncio.ensure_future(self.stop(signal))
        #         )
        #     except NotImplementedError:
        #         self.logger.warning(
        #             f"{self.name} tried to use loop.add_signal_handler "
        #             "but it is not implemented on this platform."
        #         )
        # Run hook before spider start crawling
        await self._run_spider_hook(after_start)

        # Actually run crawling
        try:
            # 基本middleware
            self.middleware.request_middleware.append(request_ua)
            # 初始化请求
            await self.start_master()

            await self.start_worker()
        finally:
            # Run hook after spider finished crawling
            await self._run_spider_hook(before_stop)
            # Display logs about this crawl task
            end_time = datetime.now()
            self.logger.info(
                f"Total requests: {self.failed_counts + self.success_counts}"
            )

            if self.failed_counts:
                self.logger.info(f"Failed requests: {self.failed_counts}")
            self.logger.info(f"Time usage: {end_time - start_time}")
            self.logger.info("Spider finished!")

    @staticmethod
    async def cancel_all_tasks():
        """
        Cancel all tasks
        :return:
        """
        tasks = []
        for task in async_all_tasks():
            if task is not async_current_task():
                tasks.append(task)
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    def start(
            cls,
            middleware: typing.Union[typing.Iterable, Middleware] = None,
            loop=None,
            after_start=None,
            before_stop=None,
            close_event_loop=True,
            **spider_kwargs,
    ):
        """
        Start a spider
        :param after_start: hook
        :param before_stop: hook
        :param middleware: customize middleware or a list of middleware
        :param loop: event loop
        :param close_event_loop: bool
        :param spider_kwargs: Additional keyword args to initialize spider
        :return: An instance of :cls:`Spider`
        """
        loop = loop or asyncio.new_event_loop()
        spider_ins = cls(middleware=middleware, loop=loop, **spider_kwargs)

        str1 = spider_ins._start(after_start=after_start, before_stop=before_stop)
        spider_ins.loop.run_until_complete(str1)
        # Actually start crawling
        # spider_ins.loop.run_until_complete(
        #     spider_ins._start(after_start=after_start, before_stop=before_stop)
        # )

        spider_ins.loop.run_until_complete(spider_ins.loop.shutdown_asyncgens())
        if close_event_loop:
            spider_ins.loop.close()

        return spider_ins

    async def handle_callback(self, aws_callback: typing.Coroutine, response):
        """
        Process coroutine callback function
        """
        callback_result = None

        try:
            callback_result = await aws_callback
        except NothingMatchedError as e:
            self.logger.exception(f"<Item: {str(e).lower()}>")
        except Exception as e:
            self.logger.exception(f"<Callback[{aws_callback.__name__}]: {e}")

        return callback_result, response

    # 从此开始
    async def handle_request(
            self, request: Request, semaphore):
        """
        Wrap request with middleware.
        :param semaphore:
        :param request:
        :return:
        """

        try:
            # 请求中间件
            await self._run_request_middleware(request)
            # 发送请求，调用回调函数
            # callback_result, response = await request.fetch_callback()
            response = await DownloadHandler().fetch(request)
            semaphore.release()
            # 响应后中间件
            await self._run_response_middleware(request, response)
            # 统计成功，失败次数

            await self._process_response(request=request, response=response)

        except NotImplementedParseError as e:
            self.logger.exception(e)
        except NothingMatchedError as e:
            error_info = f"<Field: {str(e).lower()}" + f", error url: {request.url}>"
            self.logger.exception(error_info)
        except Exception as e:
            self.logger.exception(f"<Callback[{request.callback.__name__}]: {e}")

    async def start_requests(self):
        """
        :param: start_request
        """
        for url in self.start_urls:
            yield self.request(url=url, callback=self.parse)

    async def parse(self, response):
        """
        Default callback function
        :param response: Response
        :return:
        """
        raise NotImplementedParseError("<!!! parse function is expected !!!>")

    def request(
            self,
            url: str,
            method: str = "GET",
            params: dict = None,
            data: dict = None,
            cookies: dict = None,
            callback=None,
            encoding: typing.Optional[str] = None,
            headers: dict = None,
            meta: dict = None,
            request_config: dict = None,
            **aiohttp_kwargs,
    ):
        """
        Init a Request class for crawling html
        :param cookies:
        :param data:
        :param params:
        :param url:
        :param method:
        :param callback:
        :param encoding:
        :param headers:
        :param meta:
        :param request_config:
        :param aiohttp_kwargs:
        :return:
        """
        headers = headers or {}
        meta = meta or {}
        callback = callback or self.parse
        request_config = request_config or {}

        request_config.update(self.request_config.copy())
        aiohttp_kwargs.update(self.aiohttp_kwargs.copy())

        return Request(
            url=url,
            method=method,
            params=params,
            data=data,
            cookies=cookies,
            callback=callback,
            encoding=encoding,
            headers=headers,
            meta=meta,
            request_config=request_config,
            **aiohttp_kwargs,
        )

    async def start_master(self):
        """
        Actually start crawling
        """
        async for request_ins in self.start_requests():
            self.request_queue.put_nowait(request_ins)

    async def start_worker(self):
        """
        Start spider worker
        :return:
        """
        semaphore = asyncio.Semaphore(value=self.concurrency)
        while True:
            # 不断获取一个请求
            request_item = await self.get_request()
            if request_item is None:
                await asyncio.sleep(self.wait_time)
                tasks = asyncio.all_tasks(self.loop)
                self.logger.debug('not have new request, now loop has %s task' % tasks.__len__())

                if not await self.queue_tasks() and len(tasks) <= 1:
                    self.logger.info('Stop Spider')
                    break
                continue

            await semaphore.acquire()
            await asyncio.sleep(self.request_config.get('DELAY', 0))
            # 执行请求
            self.loop.create_task(
                self.handle_request(request_item, semaphore)
            )

    async def get_request(self):
        try:
            request = self.request_queue.get_nowait()
        except asyncio.queues.QueueEmpty:
            request = None
        return request

    async def queue_tasks(self):
        """
        judge has task
        :param:
        :return:
        """
        return self.request_queue.qsize() > 0

    async def stop(self, _signal):
        """
        Finish all running tasks, cancel remaining tasks.
        :param _signal:
        :return:
        """
        self.logger.info(f"Stopping spider: {self.name}")
        await self.cancel_all_tasks()
