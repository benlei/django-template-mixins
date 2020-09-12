from django import template


class MixinNode(template.Node):
    def render(self, context):
        return ''
