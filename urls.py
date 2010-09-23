from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^djblogkit/', include('djblogkit.blog.urls')),
    (r'^admin/(.*)', admin.site.root),
)
