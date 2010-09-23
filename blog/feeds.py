# -*- encoding: utf8 -*-
import re
from django.conf import settings

from django.contrib.syndication.feeds import Feed
from djblogkit.blog.models import Entry

class DjblogkitRss(Feed):
    title = settings.BLOG_TITLE
    link = settings.BLOG_BASE
    description = u"DjangoやらPloneやらJavaやら湘南やらのお話です。"
    tag = ''

    def items(self):
        if len(self.tag) > 0 :
            return Entry.public_objects.order_by('-create_date').filter(tags__name__iexact=self.tag)[:settings.NUM_IN_RSS]
        return Entry.public_objects.order_by('-create_date')[:settings.NUM_IN_RSS]

    def item_pubdate(self, item):
        return item.create_date

    def item_link(self, item):
        return item.get_absolute_url()
        
    def item_categories(self, item):
        return [t.name for t in item.tags.all()]

    def author_name(self, item):
        if item :
            return item.author
        return self.title

