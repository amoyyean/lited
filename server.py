"""启动文件
并实现握手和通信功能"""
from tornado import ioloop
import tornado.web
from custom import secret_websocket_connect
from settings import *


async def register():
    """ lite 服务器启动时自动注册到主服务器 """
    swc = await secret_websocket_connect('ws://%s/api/v1/register' % SERVER_MASTER)
    resp = await swc.read_message()
    print(resp)
    while True:
        # 接收主服务器推送的消息
        message = await swc.read_message()
        if message:
            # 此处可以根据消息作出不同的响应
            print(message)
            pass


if __name__ == "__main__":

    app = tornado.web.Application(debug=False)
    app.listen(PORT)
    loop = ioloop.IOLoop.current()
    loop.run_sync(register)
    loop.start()
