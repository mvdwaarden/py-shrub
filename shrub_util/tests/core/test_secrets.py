from shrub_util.core.secrets import Secrets
from shrub_util.test.context import Context


def test_ut_secrets_getattr():
    with Context() as tc:
        tc.set_secrets_file(
            """
[Application1]
User=Value1
Password=PW1

[Application2]
User=Value2
Password=PW2
                """
        )
        secrets = Secrets()
        assert secrets.get_secret("Application1", "User") == "Value1"
        assert secrets.get_secret("Application1", "Password") == "PW1"
        assert secrets.get_secret("Application2", "User") == "Value2"
        assert secrets.get_secret("Application2", "Password") == "PW2"
