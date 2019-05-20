"""启动文件
并实现握手和通信功能"""
import json
from tornado import ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
from settings import *


async def register():
    """ lite服务器启动时自动注册到主服务器 """
    url = 'http://' + SERVER_MASTER + '/api/v1/reg' + "?secret=%s&port=%s" % (SERVER_SECRET_KEY, PORT)
    client = AsyncHTTPClient()
    resp = await client.fetch(url)
    print(json.loads(resp.body))


if __name__ == "__main__":

    app = tornado.web.Application(debug=False)
    app.listen(PORT)
    loop = ioloop.IOLoop.current()
    loop.run_sync(register)
    loop.start()
