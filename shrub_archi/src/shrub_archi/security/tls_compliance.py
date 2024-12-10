import OpenSSL.SSL
import socket
from typing import List
from enum import Enum


class SslMethod(Enum):
    SSL_2_3 = OpenSSL.SSL.SSLv23_METHOD
    TLS_1_1 = OpenSSL.SSL.TLSv1_1_METHOD
    TLS_1_2 = OpenSSL.SSL.TLSv1_2_METHOD


def test_endpoint_compliance(hostname: str, endpoint: str, port: int, methods: List[SslMethod]) -> str:
    for method in methods:
        ctx = OpenSSL.SSL.Context(method=method.value)
        sess = OpenSSL.SSL.Session(ctx)
        conn = sess.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
        try:
            conn.connect((endpoint, port))
        except Exception as ex:
            print(ex)

