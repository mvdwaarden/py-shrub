import collections
import enum
import hashlib
import hmac
import secrets
import urllib
from collections import OrderedDict

from shrub_util.core.dict_func import flatten_dictionary


class HashAlgorithm(enum.Enum):
    SHA256 = "SHA256"
    SHA384 = "SHA384"
    SHA512 = "SHA512"

    @staticmethod
    def from_string(algo: str):
        lookup = {
            "sha256": HashAlgorithm.SHA256,
            "sha384": HashAlgorithm.SHA384,
            "sha512": HashAlgorithm.SHA512,
        }
        algo_lookup_key = HashAlgorithm.SHA512
        if algo is not None:
            algo_lookup_key = algo.lower()

        if algo_lookup_key in lookup:
            return lookup[algo_lookup_key]
        else:
            return HashAlgorithm.SHA512

    def get_constructor(self):
        if self.value == HashAlgorithm.SHA256.value:
            return hashlib.sha256
        elif self.value == HashAlgorithm.SHA384.value:
            return hashlib.sha384
        elif self.value == HashAlgorithm.SHA512.value:
            return hashlib.sha512


class Signer:
    def __init__(self, key: bytes = None, algorithm=HashAlgorithm.SHA512):
        self.key = key
        self.algorithm = algorithm

    def create_key(self):
        if self.key is None:
            self.key = bytes(
                self.algorithm.get_constructor()(
                    bytes("spamalot", "utf-8") + secrets.token_bytes(512)
                ).hexdigest(),
                "utf-8",
            )
        return self

    def sign(self, data):
        return hmac.new(
            key=self.key,
            msg=bytes(self.to_signable_data(data), "utf-8"),
            digestmod=self.algorithm.get_constructor(),
        ).hexdigest()

    def to_signable_data(self, data) -> bytes:
        """Converts a dictionary to a URL query string, so that it used for signing"""
        if type(data) is dict or type(data) is OrderedDict:
            flattened_dict = flatten_dictionary(data)
            # sort the flattened dictionary by its keys
            ordered_signable_dict = collections.OrderedDict()
            sorted_keys = sorted(flattened_dict.keys())
            for key in sorted_keys:
                ordered_signable_dict[key] = flattened_dict[key]

            result = urllib.parse.urlencode(ordered_signable_dict)
        return result
