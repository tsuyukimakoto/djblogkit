from django import forms
from django.db import models
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.core import validators, serializers
from django.core.exceptions import ObjectDoesNotExist
from django.template.context import RequestContext
from django.contrib.syndication.views import feed
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.utils.translation import gettext as _

from djblogkit.blog.models import Entry, Comment, Trackback, RelatedItem
from djblogkit.blog.urls import tag_feeds, tag_feeds

from datetime import datetime
from datetime import date as ddate
from datetime import time as dtime
import time
import operator

from djangoripple.decorators import generic_json

def tag_feed(request, url, tag) :
    tag_feeds[url].tag = tag
    return feed(request, url, feed_dict=tag_feeds)

def is_valid_answer(data, form) :
    if form.get('valid_answer').upper() != data.upper() :
        raise validators.ValidationError, _('Your answer is not correct. Try it again!')

def getEntry(year, month, day, slug) :
    try:
        d = ddate(*time.strptime(year+month+day, '%Y%b%d')[:3])
    except ValueError:
        raise Http404
    e_list = Entry.public_objects.filter(slug__exact=slug,
                                  create_date__range=(datetime.combine(d, dtime.min), datetime.combine(d, dtime.max)))
    if len(e_list) == 0:
        raise Http404
    return e_list[0]

def pickup_related_items(request, content_type_id, object_id, target_content_type_id):
    max = 10
    keyword = request.REQUEST.get('keywords', '')
    result = {}
    keywords = keyword.strip().split(' ')
    exist_id_list = [v['related_object_id'] for v in RelatedItem.objects.filter(content_type__exact=content_type_id, object_id__exact=object_id, related_content_type__exact=target_content_type_id).values('related_object_id')]
    if content_type_id == target_content_type_id :
        exist_id_list += [object_id]
    target_model_class = ContentType.objects.get(pk=target_content_type_id).model_class()
    query_set = target_model_class._meta.admin.manager.all()
    if len(exist_id_list) > 0:
        query_set = query_set.exclude(id__in=exist_id_list)
    if hasattr(target_model_class._meta.admin, 'search_fields') and len(target_model_class._meta.admin.search_fields) > 0:
        for k in keywords:
            query_set = query_set.filter(reduce(operator.or_, [models.Q(**{'%s__icontains' % f: k}) for f in target_model_class._meta.admin.search_fields]))
    list_display = ['pk',]
    if hasattr(target_model_class._meta.admin, 'list_display'):
        list_display += target_model_class._meta.admin.list_display
    query_set = query_set[:max+1]
    data = []
    data = [r.render_as_add_list() for r in query_set]
    result = {'result': True, 'more': len(query_set) > max, 'amount': len(query_set),
              'content_type_id': content_type_id, 'target_content_Type_id': target_content_type_id,
              'data': data}
pickup_related_items = generic_json(pickup_related_items, ensure_ascii=True)

def current_related_items(request, content_type_id, object_id):
    current = RelatedItem.objects.filter(content_type__exact=content_type_id, object_id__exact=object_id)
    #TODO refactor
    current_item = []
    data = []
    for item in current:
        current_item += [ContentType.objects.get(pk=item.related_content_type_id).model_class()._meta.admin.manager.get(pk=item.related_object_id)]
    data = [r.render_as_del_list() for r in current_item]
    result = {'result': True, 'data': data}
    return result
current_related_items = generic_json(current_related_items, ensure_ascii=False)


def add_related_item(request, content_type_id, object_id):
    target_content_type_id = request.REQUEST.get('target_content_type_id', None)
    target_object_id = request.REQUEST.get('target_object_id', None)
    if not target_object_id or not target_content_type_id:
        result = {'result': False, 'message': _('You must specify target content type and a item.')}
    try :
        print 'content_type_id:%s' % content_type_id
        print 'object_id:%s' % object_id
        print 'target_content_type_id:%s' % target_content_type_id
        print 'target_object_id:%s' % target_object_id
        content_type = ContentType.objects.get(pk=content_type_id)
        target_content_type = ContentType.objects.get(pk=target_content_type_id)
        main_object_class = content_type.model_class()
        related_object_class = target_content_type.model_class()
        main_object = main_object_class._default_manager.get(pk=object_id)
        related_object = related_object_class._default_manager.get(pk=target_object_id)
    except ObjectDoesNotExist:
        result = {'result': False, 'message': _('some object does not exist')}
    else :
        RelatedItem.objects.get_or_create(content_type=content_type, object_id=object_id, \
                                          related_content_type=target_content_type, related_object_id=target_object_id)
        RelatedItem.objects.get_or_create(content_type=target_content_type, object_id=target_object_id, \
                                          related_content_type=content_type, related_object_id=object_id)
        result = {'result': True, 'target_content_type_id': target_content_type_id, 'target_object_id': target_object_id, 'message': _('Added Related Item.')}
add_related_item = generic_json(add_related_item, ensure_ascii=False)

def remove_related_item(request, content_type_id, object_id):
    print 'REMOVE ' * 5
    target_content_type_id = request.GET.get('target_content_type_id', None)
    target_object_id = request.GET.get('target_object_id', None)
    if not target_content_type_id or not target_object_id:
        raise Http404        
    target_forward  = RelatedItem.objects.filter(content_type=content_type_id, object_id=object_id,\
                                        related_content_type=target_content_type_id, related_object_id=target_object_id)
    target_backward = RelatedItem.objects.filter(content_type=target_content_type_id, object_id=target_object_id,\
                                        related_content_type=content_type_id, related_object_id=object_id)
    if len(target_forward) == 0 and len(target_backward) == 0:
        resutl = {'result': False, 'message': _('Already deleted.')}
    else:
        if len(target_forward) > 0:
            target_forward[0].delete()
        if len(target_backward) > 0:
            target_backward[0].delete()
        result = {'result': True, 'target_content_type_id': target_content_type_id, 'target_object_id': target_object_id, 'message': _('Delete Related Item.')}
remove_related_item = generic_json(remove_related_item, ensure_ascii=False)

def tag_list(request, tag) :
    return object_list(request, queryset=Entry.public_objects.filter(tags__name__iexact=tag).select_related(), paginate_by=settings.NUM_IN_PAGE, allow_empty=True)

def add_comment(request, year, month, day, slug) :
    if request.method == 'GET' :
        raise Http404

    CommentForm = forms.form_for_model(Comment)
    entry = getEntry(year, month, day, slug)
    if request.method == 'POST' :
        new_data = request.POST.copy()
        new_data.update({'entry': entry.id, 'valid_answer': entry.answer})
        if entry.riddle :
            CommentForm.base_fields['answer'] = forms.TextField(_('answer'), maxlength=50, is_required=True, validator_list=[is_valid_answer])
        form = CommentForm(new_data)
        if form.is_valid() :
            form.save()
            return HttpResponseRedirect('%s' % (entry.get_absolute_url(),))
    else :
        form = CommentForm()
    return render_to_response('blog/comment_form.html', dict(form=form, object=entry), context_instance=RequestContext(request))

def tbping(request, year, month, day, slug) :
    if request.POST :
        msg = ''
        error = ''
        url = request.POST['url']
        excerpt = request.POST['excerpt']
        blog_name = request.POST['blog_name']
        if len(excerpt) == 0 or len(blog_name) == 0 or len(url) == 0 :
            error = '1'
            msg = 'all arguments are required' 
        else :
            if len(blog_name) == 0 :
                error = '1'
                msg = 'blog name required'
            else :
                entry = getEntry(year, month, day, slug)
                t = Trackback(blog_name=blog_name, url=url, excerpt=excerpt, create_date=datetime.now())
                t.entry = entry
                t.save()
                msg = 'thanx!'
        response = HttpResponse(mimetype='text/xml')
        t = loader.get_template('blog/tbping.xml')
        c = Context({
            'error': error,
            'msg': msg,
        })
        response.write(t.render(c))
        return response
    else :
        return HttpResponseRedirect('%s/%s/%s/%s/%s/' % (settings.BLOG_BASE, year, month, day, slug))
