import os

import django
from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError, Engine
from django.test import SimpleTestCase

BASE_DIR = os.path.dirname(__file__)


class MixinTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        settings.configure(
            INSTALLED_APPS=(
                'django.contrib.sites',
                'mixin_templatetag',
            ),
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [os.path.join(BASE_DIR, 'templates')],
                'OPTIONS': {
                    'debug': True,
                    'builtins': [
                        'mixin_templatetag.templatetags.mixins',
                    ],
                }
            }],
            DEBUG=True,
        )
        django.setup()

        super().setUpClass()

    def test_render(self):
        context = Context({})
        result = Template("""
            {% load mixins %}
            
            {% mixin foo %}
            <div><div>{{ name }}</div><div>{{ description }}</div></div>
            {% endmixin %}
            {% mix foo with name="hello" description="world" %}
            ----
            {% mix foo with name="good" description="bye" %}
        """).render(context)

        expected = """
            <div><div>hello</div><div>world</div></div>
            ----
            <div><div>good</div><div>bye</div></div>
        """

        self.assertHTMLEqual(expected, result)

    def test_render_fail_mixin_not_found(self):
        with self.assertRaises(TemplateSyntaxError):
            context = Context({})
            Template("""
                {% load mixins %}
    
                {% mixin foo %}
                <div><div>{{ name }}</div><div>{{ description }}</div></div>
                {% endmixin %}
                {% mix foob with name="hello" description="world" %}
            """).render(context)

    def test_extend_for_reference(self):
        engine = Engine.get_default()
        template = engine.get_template('content.html')
        output = template.render(Context(dict(my_var='yes')))
        self.assertHTMLEqual(output, """
            <body>
                <div>DEFAULT_FOO</div>
                <div>DEFAULT_BAR</div>
            </body>
            <body>
                <div>DEFAULT_FOO:(</div>
                my way
            </body>
            <body>
                highway
                <div>DEFAULT_BARyes</div>
            </body>
            <body>
                abc
                efg
            </body>
            <body>
                421
                <div>5683</div>
            </body>
            <body>
                :)
                <div>DEFAULT_BARyes</div>
            </body>
        """)

    def test_sub_components(self):
        template = Template("""
            <main>
                {% component 'sub_component_main.html' %}
                    {% slot main_slot %}<h1>custom main_slot</h1>{% endslot %}
                {% endcomponent %}
            </main>
        """)
        rendered = template.render(Context({}))
        self.assertHTMLEqual(rendered, """
            <main>
                <div>
                    <h1>custom main_slot</h1>
                    <p>custom sub_slot</p>
                </div>
            </main>
        """)

    def test_sub_components_in_slot(self):
        template = Template("""
            <main>
                {% component 'sub_component_main.html' %}
                    {% slot main_slot %}
                        {% component 'sub_component_sub2.html' %}
                            {% slot sub2_slot %}custom sub2_slot from main_slot{% endslot %}
                        {% endcomponent %}
                    {% endslot %}
                {% endcomponent %}
            </main>
        """)
        rendered = template.render(Context({}))
        self.assertHTMLEqual(rendered, """
            <main>
                <div>
                    <span>custom sub2_slot from main_slot</span>
                    <p>custom sub_slot</p>
                </div>
            </main>
        """)

    def test_component_with_include(self):
        template = Template("""
            <main>
                {% component 'component_includes.html' %}
                    {% slot test_slot %}<h1>custom test_slot</h1>{% endslot %}
                {% endcomponent %}
            </main>
        """)
        rendered = template.render(Context({}))
        self.assertHTMLEqual(rendered, """
            <main>
                <div>included html</div>
                <div>
                    <h1>custom test_slot</h1>
                </div>
            </main>
        """)

    def test_component_with_include_in_slot(self):
        template = Template("""
            <main>
                {% component 'component_includes.html' %}
                    {% slot test_slot %}{% include 'include_test.html' %}{% endslot %}
                {% endcomponent %}
            </main>
        """)
        rendered = template.render(Context({}))
        self.assertHTMLEqual(rendered, """
            <main>
                <div>included html</div>
                <div>
                    <div>included html</div>
                </div>
            </main>
        """)

