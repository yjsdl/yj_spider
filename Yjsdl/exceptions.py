# -*- coding: utf-8 -*-
# @Time    : 2022/8/22 17:31
# @Author  : Liuyijie
# @File    : exceptions.py


class IgnoreThisItem(Exception):
    pass


class InvalidCallbackResult(Exception):
    pass


class InvalidFuncType(Exception):
    pass


class InvalidRequestMethod(Exception):
    pass


class NotImplementedParseError(Exception):
    pass


class NothingMatchedError(Exception):
    pass


class SpiderHookError(Exception):
    pass
