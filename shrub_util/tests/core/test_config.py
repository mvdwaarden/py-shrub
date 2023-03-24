from shrub_util.core.config import Config
from shrub_util.test.context import Context


def test_ut_config_getattr():
    with Context() as tc:
        tc.set_config_file(
            """
[Section1]
Key1=Value1
Key2=String1
Key3=1
Key4=true

[Section2]
Key1=Value12
Key2=String12
Key3=12
Key4=false
        """
        )
        cfg = Config()
        section1 = cfg.get_section("Section1")
        section2 = cfg.get_section("Section2")
        assert section1.get_setting("Key1") == "Value1"
        assert section1.get_setting("Key2") == "String1"
        assert section1.get_setting("Key3") == "1"
        assert section1.get_setting("Key4") == "true"
        assert section2.get_setting("Key1") == "Value12"
        assert section2.get_setting("Key2") == "String12"
        assert section2.get_setting("Key3") == "12"
        assert section2.get_setting("Key4") == "false"
