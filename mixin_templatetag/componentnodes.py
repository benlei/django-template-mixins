from collections import defaultdict

from django.template import TemplateSyntaxError, Node, Template, Variable
from django.template.loader_tags import ExtendsNode, IncludeNode
from django.utils.safestring import mark_safe

SLOT_CONTEXT_KEY = 'slot_context'


class SlotContext:
    def __init__(self):
        # Dictionary of FIFO queues.
        self.slots = defaultdict(list)

    def add_slots(self, slots):
        for name, slot in slots.items():
            self.slots[name].insert(0, slot)

    def pop(self, name):
        try:
            return self.slots[name].pop()
        except IndexError:
            return None

    def push(self, name, slot):
        self.slots[name].append(slot)

    def get_slot(self, name):
        try:
            return self.slots[name][-1]
        except IndexError:
            return None


class ComponentNode(Node):
    context_key = 'component_context'

    def __init__(self, nodelist, parent_name, extra_context=None, isolated_context=False):
        self.extra_context = extra_context
        self.isolated_context = isolated_context
        self.nodelist = nodelist
        self.parent_name = parent_name
        # self.template_dirs = template_dirs
        self.slots = {n.name: n for n in nodelist.get_nodes_by_type(SlotNode)}

    def __repr__(self):
        return '<Component Node: %s %s>' % (self.__class__.__name__, self.parent_name.token)

    def find_template(self, template_name, context):
        template, origin = context.template.engine.find_template(
            template_name
        )
        return template

    def get_parent(self, context):
        parent = self.parent_name.resolve(context)
        if not parent:
            error_msg = "Invalid template name in 'component' tag: %r." % parent
            if self.parent_name.filters or \
                    isinstance(self.parent_name.var, Variable):
                error_msg += " Got this from the '%s' variable." % \
                             self.parent_name.token
            raise TemplateSyntaxError(error_msg)
        if isinstance(parent, Template):
            # parent is a django.template.Template
            return parent
        if isinstance(getattr(parent, 'template', None), Template):
            # parent is a django.template.backends.django.Template
            return parent.template
        return self.find_template(parent, context)

    def render(self, context):
        compiled_parent = self.get_parent(context)

        if SLOT_CONTEXT_KEY not in context.render_context:
            context.render_context[SLOT_CONTEXT_KEY] = SlotContext()
        slot_context = context.render_context[SLOT_CONTEXT_KEY]

        # Add the block nodes from this node to the block context
        slot_context.add_slots(self.slots)

        # If this block's parent doesn't have an extends node it is the root,
        # # and its block nodes also need to be added to the block context.
        for node in compiled_parent.nodelist:
            # The ExtendsNode has to be the first non-text node.
            if isinstance(node, ExtendsNode):
                raise TemplateSyntaxError("%s must not extend another template" % (self))

        # Call Template._render explicitly so the parser context stays
        # the same.
        values = {
            name: var.resolve(context)
            for name, var in self.extra_context.items()
        }

        with context.render_context.push_state(compiled_parent, isolated_context=False):
            if self.isolated_context:
                return compiled_parent._render(context.new(values))
            with context.push(**values):
                return compiled_parent._render(context)


class SlotNode(Node):
    def __init__(self, name, nodelist, parent=None):
        self.name, self.nodelist, self.parent = name, nodelist, parent

    def __repr__(self):
        return "<Slot Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        slot_context = context.render_context.get(SLOT_CONTEXT_KEY)
        with context.push():
            if slot_context is None:
                context['slot'] = self
                result = self.nodelist.render(context)
            else:
                slot = slot_context.pop(self.name)
                if slot is None:
                    slot = self
                # Create new block so we can store context without thread-safety issues.
                slot = type(self)(slot.name, slot.nodelist)
                slot.context = context
                context['slot'] = slot
                result = slot.nodelist.render(context)
                # if push is not None:
                #     slot_context.push(self.name, push)
        return result

    def super(self):
        if not hasattr(self, 'context'):
            raise TemplateSyntaxError(
                "'%s' object has no attribute 'context'. Did you use "
                "{{ slot.super }} in a base template?" % self.__class__.__name__
            )
        render_context = self.context.render_context
        if (SLOT_CONTEXT_KEY in render_context and
                render_context[SLOT_CONTEXT_KEY].get_slot(self.name) is not None):
            return mark_safe(self.render(self.context))
        return ''
