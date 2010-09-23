from django.conf.urls.defaults import *
from django.conf import settings

from django.utils.functional import lazy

from djblogkit.blog.models import Entry, Archive, Comment, Trackback, Tag
from djblogkit.blog.feeds import DjblogkitRss

feeds = {
    'rss': DjblogkitRss
}
tag_feeds = {
    'rss': DjblogkitRss
}

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.list_detail.object_list', dict(queryset=Entry.public_objects.all().select_related(), paginate_by=settings.NUM_IN_PAGE, allow_empty=True)),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>.*)/add_comment/$', 'djblogkit.blog.views.add_comment',),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>.*)/tbping/$', 'djblogkit.blog.views.tbping',),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>.*)/$', 'django.views.generic.date_based.object_detail', dict(queryset=Entry.public_objects.all().select_related(), date_field='create_date', slug_field='slug')),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$', 'django.views.generic.date_based.archive_day', dict(queryset=Entry.public_objects.all().select_related(), date_field='create_date')),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$', 'django.views.generic.date_based.archive_month', dict(queryset=Entry.public_objects.all().select_related(), date_field='create_date')),
    (r'^tag/(?P<tag>.*)/$', 'djblogkit.blog.views.tag_list'),
    (r'^related/search/(?P<content_type_id>\d+)/(?P<object_id>\d+)/(?P<target_content_type_id>\d+)/$', 'djblogkit.blog.views.pickup_related_items'),
    (r'^related/current/(?P<content_type_id>\d+)/(?P<object_id>\d+)/$', 'djblogkit.blog.views.current_related_items'),
    (r'^related/add/(?P<content_type_id>\d+)/(?P<object_id>\d+)/$', 'djblogkit.blog.views.add_related_item'),
    (r'^related/remove/(?P<content_type_id>\d+)/(?P<object_id>\d+)/$', 'djblogkit.blog.views.remove_related_item'),
    #RSS
    #url must be rss
    (r'^feed/(?P<url>.*)/(?P<tag>.*)/$', 'djblogkit.blog.views.tag_feed'),
    (r'^feed/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

)
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
)
