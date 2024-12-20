import ssl
from enum import Enum
from typing import Optional, Any


class SslMethod(Enum):
    SSL_2_3 = ssl.PROTOCOL_SSLv23
    TLS_1_1 = ssl.PROTOCOL_TLSv1_1
    TLS_1_2 = ssl.PROTOCOL_TLSv1_2


class EndpointComplianceInfo:
    def __init__(self, endpoint, port, method):
        self.endpoint = endpoint
        self.port = port
        self.forced_method: Optional[SslMethod] = method
        self.negotiated_method: Optional[Any] = None
        self.ciphers: Optional[Any] = None
        self.peer_certificate: Optional[Any] = None
        self.error: Optional[Exception] = None
        self.reference_number: Optional[str] = None
        self.description: Optional[str] = None
        self.owner: Optional[str] = None
        self.environment: Optional[str] = None

    def set_from_socket(self, ssock):
        self.negotiated_method = ssock.version()
        self.ciphers = ssock.cipher()
        self.peer_certificate = ssock.getpeercert()

    def to_str(self) -> str:
        return f"""
            reference_number: {self.reference_number}
            endpoint: {self.endpoint}:{self.port}
            environment: {self.environment}
            forced method: {self.forced_method}
            negotiated method: {self.negotiated_method}
            cyphers: {self.ciphers}
            error: {self.error}"""

    @staticmethod
    def get_csv_header():
        return ["reference_number", "endpoint", "port", "environment", "forced_method", "negotiated_method", "ciphers", "error"]

    def get_csv_row(self):
        return [self.reference_number, self.endpoint, self.port, self.environment, self.forced_method, self.negotiated_method, self.ciphers,
                self.error]
