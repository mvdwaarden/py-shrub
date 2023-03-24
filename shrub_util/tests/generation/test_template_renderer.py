from shrub_util.generation.template_renderer import TemplateRenderer
from shrub_util.test.context import Context


def test_it_template_renderer_1():
    with Context() as tc:
        tc.set_template("template.j2", "{% for item in list %}{{item}},{% endfor %}")
        renderer = TemplateRenderer()
        result = renderer.render("template.j2", list=[1, 2, "s1", "s2"])
        print(f"rendered {result}")
        assert result == "1,2,s1,s2,"
