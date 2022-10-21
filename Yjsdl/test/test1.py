# -*- coding: utf-8 -*-
# @Time    : 2022/10/12 22:58
# @Author  : Liuyijie
# @File    : test1.py


mongodb_config = {"host": "127.0.0.1", "port": 27017, "db": "ruia_motor"}


account="{username}:{password}@".format(username=mongodb_config["username"],
                                            password=mongodb_config["password"],
                                            ) if mongodb_config.get("username") else ""

motor_uri = "mongodb://{account}{host}:{port}/{database}".format(
    account="{username}:{password}@".format(username=mongodb_config["username"],
                                            password=mongodb_config["password"],
                                            )
    if mongodb_config.get("username")
    else "",
    host=mongodb_config.get("host", "localhost"),
    port=mongodb_config.get("port", 271017),
    database=mongodb_config.get("db", "admin"),
    )

# print(motor_uri)



# def foo(n):
#     print('start')
#     for i in range(n):
#         yield i
#
# bb = 2
#
# g = foo(bb)

import Yjsdl.field as f



class Test:
    def __init__(self):
        self.data = []

    def test1(self):
        a = '1'

    async def test2(self):
        b = '2'
c = Test()

print(c.test2())
