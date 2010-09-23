from django.template import Node, Library
from djblogkit.blog.models import Relatable, RelatedItem

register = Library()

class RelatableNode(Node):
    def __init__(self, variable):
        self.variable = variable
        
    def render(self, context):
        context[self.variable] = Relatable.objects.all().order_by('id').select_related()
        return ''

class RelatedObjectsNode(Node) :
    def __init__(self, variable, content_type_id, object_key):
        self.variable = variable
        self.content_type_id = content_type_id
        self.object_key = object_key


    def render(self, context):
        real_items = []
        items = RelatedItem.objects.select_related(True).filter(content_type__exact=context[self.content_type_id], object_id__exact=context[self.object_key].id)
        for item in items:
            real_items.append(item.related_content_type.get_object_for_this_type(id__exact=item.related_object_id))
        context[self.variable] = real_items
        return ''

def do_get_relatable_list(parser, token):
    """
    {% get_relatable_list as relatable_list %}
    """
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "'%s' tag takes two arguments" % bits[0]
    if bits[1] != "as":
        raise template.TemplateSyntaxError, "First argument to '%s' tag must be 'as'" % bits[0]
    return RelatableNode(bits[2])
register.tag('get_relatable_list', do_get_relatable_list)

def do_get_related_objects(parser, token) :
    """
    {% get_related_objects with object of content_type_id as related_objects %}
    """
    bits = token.contents.split()
    if len(bits) != 7:
        raise template.TemplateSyntaxError, "'%s' tag takes four arguments" % bits[0]
    return RelatedObjectsNode(bits[6], bits[4], bits[2])
register.tag('get_related_objects', do_get_related_objects)
