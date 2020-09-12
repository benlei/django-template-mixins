from django import template


class MixNode(template.Node):
    def __init__(self, nodelist, *args, extra_context=None, isolated_context=False, **kwargs):
        self.nodelist = nodelist
        self.extra_context = extra_context or {}
        self.isolated_context = isolated_context
        super().__init__(*args, **kwargs)

    def render(self, context):
        values = {
            name: var.resolve(context)
            for name, var in self.extra_context.items()
        }

        if self.isolated_context:
            return self.nodelist.render(context.new(values))
        with context.push(**values):
            return self.nodelist.render(context)
