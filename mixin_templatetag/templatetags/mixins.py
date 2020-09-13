from django import template
from django.template import TemplateSyntaxError
from django.template.base import token_kwargs, TextNode
from django.template.defaulttags import CommentNode
from django.template.loader_tags import construct_relative_path

from mixin_templatetag.componentnodes import SlotNode, ComponentNode
from mixin_templatetag.mixinnodes import MixinNode, MixNode

register = template.Library()


def parse_options(bits, options, parser):
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})  # bits[1] = construct_relative_path(parser.origin.template_name, bits[1])
    return isolated_context, namemap


@register.tag('mixin')
def do_mixinblock(parser, token):
    """
    Mostly copied from the do_block; stores the nodelist into a var
    """
    # token.split_contents() isn't useful here because this tag doesn't accept variable as arguments
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag takes only one argument" % bits[0])
    block_name = bits[1]
    # Keep track of the names of BlockNodes found in this template, so we can
    # check for duplication.
    try:
        if block_name in parser.__loaded_mixins:
            raise TemplateSyntaxError("'%s' tag with name '%s' appears more than once" % (bits[0], block_name))
        parser.__loaded_mixins.append(block_name)
    except AttributeError:  # parser.__loaded_mixins isn't a list yet
        parser.__loaded_mixins = [block_name]
    nodelist = parser.parse(('endmixin',))

    # This check is kept for backwards-compatibility. See #3100.
    endblock = parser.next_token()
    acceptable_endblocks = ('endmixin', 'endmixin %s' % block_name)
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, 'endmixin', acceptable_endblocks)

    try:
        parser.__mixins[block_name] = nodelist
    except AttributeError:  # parser.__mixins isn't a list yet
        parser.__mixins = {block_name: nodelist}

    return MixinNode()


@register.tag('mix')
def do_mix(parser, token):
    """
    Load a template and render it with the current context. You can pass
    additional context using keyword arguments.
    Example::
        {% mix foo %}
        {% mix foo with bar="BAZZ!" baz="BING!" %}
    Use the ``only`` argument to exclude the current context when rendering
    the mixin::
        {% mix foo only %}
        {% mix foo with bar="1" only %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )

    mixin_name = bits[1]

    if mixin_name not in parser.__mixins:
        raise TemplateSyntaxError("'%s' tag with mixin '%s' cannot be found." % (bits[0], mixin_name))

    options = {}
    isolated_context, namemap = parse_options(bits, options, parser)
    return MixNode(nodelist=parser.__mixins[mixin_name], extra_context=namemap, isolated_context=isolated_context)


@register.tag('component')
def do_component(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    bits[1] = construct_relative_path(parser.origin.template_name, bits[1])
    parent_name = parser.compile_filter(bits[1])

    nodelist = parser.parse(('endcomponent',))

    # This check is kept for backwards-compatibility. See #3100.
    endblock = parser.next_token()
    acceptable_endblocks = ('endcomponent')
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, 'endcomponent', acceptable_endblocks)

    for node in nodelist:
        if isinstance(node, TextNode) and len(node.s.strip()) == 0 or isinstance(node, CommentNode):
            # whitespace/comments are a-ok
            continue

        # The ExtendsNode has to be the first non-text node.
        if not isinstance(node, SlotNode):
            raise TemplateSyntaxError("'%s' only allows slots" % bits[0])

    options = {}
    isolated_context, namemap = parse_options(bits, options, parser)
    return ComponentNode(nodelist, parent_name, extra_context=namemap, isolated_context=isolated_context)


@register.tag('slot')
def do_slot(parser, token):
    """
    Define a block that can be overridden by child templates.
    """
    # token.split_contents() isn't useful here because this tag doesn't accept variable as arguments
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag takes only one argument" % bits[0])
    block_name = bits[1]

    nodelist = parser.parse(('endslot',))

    # This check is kept for backwards-compatibility. See #3100.
    endblock = parser.next_token()
    acceptable_endblocks = ('endslot', 'endslot %s' % block_name)
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, 'endslot', acceptable_endblocks)

    return SlotNode(block_name, nodelist)
