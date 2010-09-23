from django.conf import settings

from djblogkit.blog.models import Entry, Archive, Comment, Trackback, Tag, Relatable


_djblogkit_context = locals()
def djblogkit_context(request):
    """
    Returns context variables required by apps that use Django's authentication
    system.
    """
    r_list = _djblogkit_context.get('related_content_type_list', None)
    if not r_list:
        r_list = Relatable.objects.all().select_related()
        _djblogkit_context['related_content_type_list'] = r_list
    context_dict = {
        'BLOG_TITLE': settings.BLOG_TITLE,
        'BLOG_BASE': settings.BLOG_BASE,
        'MEDIA_URL': settings.MEDIA_URL,
        'entry_list': Entry.public_objects.order_by('-create_date')[:settings.LIST_COUNT],
        'archive_list': Archive.objects.order_by('yearmonth'),
        'comment_list': Comment.objects.select_related().order_by('-create_date')[:settings.LIST_COUNT],
        'trackback_list': Trackback.objects.select_related().order_by('-create_date')[:settings.LIST_COUNT],
        'tag_list': Tag.objects.order_by('name'),
    }
    for r in r_list:
        context_dict['%s_%s' % (r.content_type.app_label, r.content_type.model)] = r.content_type.id
    return context_dict
