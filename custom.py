"""在握手时发送密钥和端口号"""
import os
import base64
from tornado.queues import Queue
from tornado.concurrent import Future
from tornado.tcpclient import TCPClient
from tornado import httpclient, httputil
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketClientConnection

from settings import SERVER_SECRET_KEY, PORT


_default_max_message_size = 10 * 1024 * 1024


class SecretWebSocketConnection(WebSocketClientConnection):
    """在原基础上新增SERVER_SECRET_KEY和PORT"""

    def __init__(self, request, on_message_callback=None,
                 compression_options=None, ping_interval=None, ping_timeout=None,
                 max_message_size=None, subprotocols=[]):
        self.compression_options = compression_options
        self.connect_future = Future()
        self.protocol = None
        self.read_queue = Queue(1)
        self.key = base64.b64encode(os.urandom(16))
        self._on_message_callback = on_message_callback
        self.close_code = self.close_reason = None
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_message_size = max_message_size

        scheme, sep, rest = request.url.partition(':')
        scheme = {'ws': 'http', 'wss': 'https'}[scheme]
        request.url = scheme + sep + rest
        request.headers.update({
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Key': self.key,
            'Sec-WebSocket-Version': '13',
        })
        # 新增SERVER_SECRET_KEY
        request.headers['Server-Secret-Key'] = SERVER_SECRET_KEY
        # 新增PORT
        request.headers['PORT'] = str(PORT)
        if subprotocols is not None:
            request.headers['Sec-WebSocket-Protocol'] = ','.join(subprotocols)
        if self.compression_options is not None:
            # Always offer to let the server set our max_wbits (and even though
            # we don't offer it, we will accept a client_no_context_takeover
            # from the server).
            # TODO: set server parameters for deflate extension
            # if requested in self.compression_options.
            request.headers['Sec-WebSocket-Extensions'] = (
                'permessage-deflate; client_max_window_bits')

        self.tcp_client = TCPClient()
        super(WebSocketClientConnection, self).__init__(
            None, request, lambda: None, self._on_http_response,
            104857600, self.tcp_client, 65536, 104857600)


def secret_websocket_connect(url, callback=None, connect_timeout=None,
                      on_message_callback=None, compression_options=None,
                      ping_interval=None, ping_timeout=None,
                      max_message_size=_default_max_message_size, subprotocols=None):
    """将原来的WebSocketClientConnection改成
    SecretWebSocketConnection
    """
    if isinstance(url, httpclient.HTTPRequest):
        assert connect_timeout is None
        request = url
        # Copy and convert the headers dict/object (see comments in
        # AsyncHTTPClient.fetch)
        request.headers = httputil.HTTPHeaders(request.headers)
    else:
        request = httpclient.HTTPRequest(url, connect_timeout=connect_timeout)
    request = httpclient._RequestProxy(
        request, httpclient.HTTPRequest._DEFAULTS)
    conn = SecretWebSocketConnection(request,
                                     on_message_callback=on_message_callback,
                                     compression_options=compression_options,
                                     ping_interval=ping_interval,
                                     ping_timeout=ping_timeout,
                                     max_message_size=max_message_size,
                                     subprotocols=subprotocols)
    if callback is not None:
        IOLoop.current().add_future(conn.connect_future, callback)
    return conn.connect_future