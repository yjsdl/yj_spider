#!/usr/bin/env python

import asyncio
import json

from http.cookies import SimpleCookie
from typing import Any, Callable, Optional

from lxml import etree

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

DEFAULT_JSON_DECODER = json.loads
JSONDecoder = Callable[[str], Any]


class Response(object):
    """
    Return a friendly response
    """

    def __init__(
            self,
            url: str,
            method: str,
            *,
            encoding: str = "",
            meta: dict,
            cookies,
            history,
            headers=None,
            status: int = -1,
            text=None,
            content=b''
    ):
        self._callback_result = None
        self._encoding = encoding
        self._url = url
        self._method = method
        self._meta = meta
        self._index = None
        self._html = ""
        self._cookies = cookies
        self._history = history
        self._headers = headers
        self._status = status
        self._ok = self._status == 0 or 200 <= self._status <= 299
        self._content = content

    @property
    def callback_result(self):
        return self._callback_result

    @callback_result.setter
    def callback_result(self, value):
        self._callback_result = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def ok(self) -> bool:
        return self._ok

    @ok.setter
    def ok(self, value: bool):
        self._ok = value

    @property
    def encoding(self):
        return self._encoding

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def method(self):
        return self._method

    @property
    def meta(self):
        return self._meta

    @property
    def cookies(self) -> dict:
        if isinstance(self._cookies, SimpleCookie):
            cur_cookies = {}
            for key, value in self._cookies.items():
                cur_cookies[key] = value.value
            return cur_cookies
        else:
            return self._cookies

    @property
    def history(self):
        return self._history

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def status(self):
        return self._status

    def html_etree(self, html: str, **kwargs):
        """
        Return etree HTML
        """
        html = html or self._html
        html_etree = etree.HTML(text=html, **kwargs)
        return html_etree

    async def json(
            self,
            *,
            encoding: str = None,
            loads: JSONDecoder = DEFAULT_JSON_DECODER,
            content_type: Optional[str] = "application/json",
            **kwargs
    ) -> Any:
        """Read and decodes JSON response."""
        if not encoding and self._encoding and len(self._encoding) > 3:

            encoding = encoding or self._encoding
            return json.loads(
                            self._content.decode(encoding), **kwargs)
        return json.loads(await self.text(), **kwargs)

    async def read(self) -> bytes:
        """Read response payload."""
        return self._content

    async def text(
            self, *, encoding: Optional[str] = None, errors: str = "strict"
    ) -> str:
        """Read response payload and decode."""
        encoding = encoding or self._encoding
        if not self._content:
            return ''

        self._html = str(self._content, encoding=encoding, errors=errors)
        return self._html

    def __repr__(self):
        return f"<Response url[{self._method}]: {self._url} status:{self._status}>"
