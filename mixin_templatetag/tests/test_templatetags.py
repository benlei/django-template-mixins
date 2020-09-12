import django
from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase


class MixinTest(TestCase):
    @classmethod
    def setUpClass(cls):
        settings.configure(
            INSTALLED_APPS=(
                # 'django.contrib.admin',
                # 'django.contrib.admindocs',
                # 'django.contrib.auth',
                # 'django.contrib.contenttypes',
                # 'django.contrib.messages',
                # 'django.contrib.sessions',
                'django.contrib.sites',
                # 'django.contrib.staticfiles',
                'mixin_templatetag'
            ),
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': '/tmp/test_templatetags'
                }
            },
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'OPTIONS': {
                    'debug': True
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

        self.assertEqual(expected.strip(), result.strip())

    def test_render_fail_mixin_not_found(self):
        with self.assertRaises(TemplateSyntaxError):
            context = Context({})
            result = Template("""
                {% load mixins %}
    
                {% mixin foo %}
                <div><div>{{ name }}</div><div>{{ description }}</div></div>
                {% endmixin %}
                {% mix foob with name="hello" description="world" %}
            """).render(context)
