from django import template


class MixinNode(template.Node):
    must_be_first = True

    def render(self, context):
        return ''
