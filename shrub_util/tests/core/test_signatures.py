from shrub_util.core.signatures import HashAlgorithm, Signer
from shrub_util.test.context import Context


def test_signer_simple():
    with Context() as tc:
        assert_data = {"sha256": 64, "sha384": 96, "sha512": 128}
        data = {"key2": "a1", "key1": "a2"}
        for algo in assert_data.keys():
            signer = Signer(algorithm=HashAlgorithm.from_string(algo))
            signature = signer.create_key().sign(data)
            assert signature is not None
            assert len(signature) == assert_data[algo]


def test_signer_ordering_and_nested_agnosticism():
    with Context() as tc:
        assert_data = {"sha256": 64, "sha384": 96, "sha512": 128}
        data1 = {"key2": "a1", "key1": "a2"}
        data2 = {"body": {"key2": "a1", "key1": "a2"}}
        for algo in assert_data.keys():
            signer = Signer(algorithm=HashAlgorithm.from_string(algo))
            signature1 = signer.create_key().sign(data1)
            signature2 = signer.create_key().sign(data2)
            assert signature1 == signature2


def test_no_duplicate():
    """Test if two instances of the Signer class generate different signatures"""
    with Context() as tc:
        assert_data = {"sha256": 64, "sha384": 96, "sha512": 128}
        data = {"key1": "a1", "key2": "a2"}
        for algo in assert_data.keys():
            signer = Signer(algorithm=HashAlgorithm.from_string(algo))
            signature = signer.create_key().sign(data)
            assert signature is not None
            signer2 = Signer(algorithm=HashAlgorithm.from_string(algo))
            signature2 = signer2.create_key().sign(data)
            assert signature2 is not None
            assert len(signature) == len(signature2)
            assert signature != signature2
