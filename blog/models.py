from django.db import models
from django.db.models.query import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.validators import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader, Context, TemplateDoesNotExist 
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

import os

default_related_template = os.path.join(os.path.join('blog', 'related'), 'object.html')
def render_related_obejct(related_object):
    template_name = os.path.join(os.path.join('blog', 'related'), related_object.t)
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        template = loader.get_template(default_related_template)
    context = Context({'related_object':related_object})
    return template.render(context)
 
def delete_for_related(related_object):
    ms = related_object.get_content_type()
    RelatedItem.objects.filter((Q(content_type__exact=ms.id) & Q(object_id__exact=related_object.id)) | (Q(related_content_type__exact=ms.id) & Q(related_object_id__exact=related_object.id))).delete()
    super(related_object.__class__, related_object).delete()

class RelatedItem(models.Model) :
    content_type = models.ForeignKey(ContentType, verbose_name=_('Main Content Type'), related_name='relateditem_as_main_set')
    object_id = models.IntegerField(_('main object ID'))
    related_content_type = models.ForeignKey(ContentType, verbose_name=_('Related Content Type'), related_name='relateditem_as_related_set')
    related_object_id = models.IntegerField(_('related object ID'))
    pub_date = models.DateTimeField(auto_now_add=True)

    main_object = generic.GenericForeignKey()
    related_object = generic.GenericForeignKey(ct_field='related_content_type', fk_field='related_object_id')

    unique_together = (('content_type', 'object_id', 'related_content_type', 'related_object_id'), )

    inline = False

    def get_object(self):
        try:
            return self.content_type.get_object_for_this_type(pk=self.object_id)
        except ObjectDoesNotExist:
            return None

    def get_related_object(self):
        try:
            return self.related_content_type.get_object_for_this_type(pk=self.related_object_id)
        except ObjectDoesNotExist:
            return None

    def __unicode__(self) :
        return u'%s:%s-%s:%s' % (self.content_type, self.object_id, self.related_content_type, self.related_object_id)

    def delete(self):
        super(RelatedItem, self).delete()
        try :
            exist_item = RelatedItem.objects.get(content_type=self.related_content_type, object_id=self.related_object_id,
                                                related_content_type=self.content_type, related_object_id=self.object_id)
        except ObjectDoesNotExist:
            pass
        else:
            exist_item.delete()

class RelatedModelBase(object):
    inline = False
    t = ''
    myself = None

    related_contents = generic.GenericRelation(RelatedItem)

    def as_list(self) :
        return self.__unicode__()

    def get_content_type(self):
        if not self.__class__.myself:
            self.__class__.myself = ContentType.objects.get_for_model(self.__class__)
        return self.__class__.myself

    def _add_script(self):
        return "javascript:set_related('%d','%d');return false;" % (self.get_content_type().id, self.id)

    def _del_script(self):
        return "javascript:remove_related('%d','%d');return false;" % (self.get_content_type().id, self.id)

    def _render_related(self):
        return render_related_obejct(self)
    render_related = property(_render_related)

    def render_as_add_list(self):
        return '''<div class="related_search_result" id="related_search_result_%d_%d">
<div class="related_action"><a href="#" onClick="%s"><img class="add_icon" width="24" height="24" /></a></div>
<div class="related_title">%s</div>
<div class="dummy"></div>
</div>
'''  % (self.get_content_type().id, self._get_pk_val(), self._add_script() , self.as_list(), )

    def render_as_del_list(self):
        return '''<div class="related_current_result" id="related_current_result_%d_%d">
<div class="related_action"><a href="#" onClick="%s"><img class="del_icon" width="24" height="24" /></a></div>
<div class="related_title">%s</div>
<div class="dummy"></div>
</div>
''' % (self.get_content_type().id, self._get_pk_val(), self._del_script() , self.as_list(), )

def is_relatable(field_data, all_data):
    c = ContentType.objects.get(pk=field_data).model_class()
    if not issubclass(c, RelatedModelBase):
        raise ValidationError, _("You must select Only Relatable Model(%s isn't)" % c._meta.object_name)

class Relatable(models.Model):
    content_type = models.ForeignKey(ContentType, verbose_name=_('Selected Related Model'), unique=True, validator_list=[is_relatable])

    def __unicode__(self):
        return self.content_type.name

class Archive(models.Model) :
    yearmonth = models.CharField(max_length=6, blank=False)
    ym_dict = {'01': 'jan','02': 'feb','03': 'mar',
               '04': 'apr','05': 'may','06': 'jun',
               '07': 'jul','08': 'aug','09': 'sep',
               '10': 'oct','11': 'nov','12': 'dec',}

    def __unicode__(self) :
        return self.yearmonth

    def _year(self) :
        return self.yearmonth[:4]
    year = property(_year)

    def _month(self):
        return self.yearmonth[4:6]
    month = property(_month)

    def get_path(self) :
        month = ''
        year = self.yearmonth[0:4]
        mm = self.yearmonth[4:6]
        month = Archive.ym_dict[mm]
        return '%s/%s/%s/' % (settings.BLOG_BASE, year, month)
    path = property(get_path)

    def get_absolute_url(self) :
        return self.get_path()
    absolute_url = property(get_absolute_url)

class Tag(models.Model) :
    create_date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=25, unique=True, blank=False)

    def __unicode__(self) :
        return self.name

    def get_absolute_url(self) :
        return '%s/tag/%s/' % (settings.BLOG_BASE, self.name)
    absolute_url = property(get_absolute_url)


class EntryPublicManager(models.Manager) :
    def get_query_set(self) :
        return super(EntryPublicManager, self).get_query_set().filter(visible=True)

class EntryPrivateManager(models.Manager) :
    pass

class Entry(models.Model, RelatedModelBase) :
    title = models.CharField(_('Title'), max_length=250, blank=False)
    author = models.ForeignKey(User, verbose_name=_('Author'))
    slug = models.SlugField(_('Slug'), unique_for_date='create_date', help_text=_('Use for url. You hova to input yourself if your title is not Ascii Charcters.'))
    summary = models.TextField(_('Summary'), blank=False)
    body = models.TextField(_('Body'), blank=True)
    create_date = models.DateTimeField(_('Create date'), auto_now_add=True, editable=False)
    update_date = models.DateTimeField(_('Update date'), auto_now=True, editable=False)
    visible = models.BooleanField(default=True, help_text=_('Show this entry for only logined user.'))
    ping_now = models.BooleanField(default=False, help_text=_("Ping entry info for ping sites. Attn, it doesn't work if Entry is not visible."))

    trackback_now = models.BooleanField(default=False, help_text=_("Ping trackback for tracback urls. Attn, it doesn't work if Entry is not visible."))
    trackbacked_sites = models.TextField(_('Trackback urls'), blank=True)

    tags = models.ManyToManyField(Tag, verbose_name='list of tags', blank=True)

    comment_count = models.IntegerField(_('Comment count'), default=0, editable=False)
    trackback_count = models.IntegerField(_('Trackback count'), default=0, editable=False)

    riddle = models.CharField(_('Riddle'), max_length=250, db_index=False, blank=True, help_text=_('Riddle for commenting this entry.'))
    answer = models.CharField(_('Answer'), max_length=50, db_index=False, blank=True, help_text=_("Riddle's answer. Ignore case."))

    related_contents = generic.GenericRelation(RelatedItem)

    private_objects = EntryPrivateManager()
    public_objects = EntryPublicManager()

    def __unicode__(self) :
        return self.title

    def trackback_array(self) :
        return self.trackback_set.order_by('create_date')

    def comment_array(self) :
        return self.comment_set.order_by('create_date')

    def get_absolute_url(self):
        return '%s/%s/%s/' % (settings.BLOG_BASE, self.create_date.strftime('%Y/%b/%d').lower(), self.slug)
    absolute_url = property(get_absolute_url)

    def get_month_url(self) :
        return '%s/%s/' % (settings.BLOG_BASE, self.create_date.strftime('%Y/%b').lower())
    month_url = property(get_month_url)

    def _get_day_url(self) :
        return '%s/%s/' % (settings.BLOG_BASE, self.create_date.strftime('%Y/%b/%d').lower())
    day_url = property(_get_day_url)

    def _create_month(self) :
        return '%4d/%02d' % (self.create_date.year, self.create_date.month)
    create_month = property(_create_month)

    def save(self):
        self.should_tb = self.trackback_now and self.visible and len(self.trackbacked_sites.strip()) > 0
        self.should_ping = self.ping_now and self.visible
        self.trackback_now = False
        self.ping_now = False
        super(Entry, self).save()
        Archive.objects.get_or_create(yearmonth='%4d%02d' % (self.create_date.year, self.create_date.month))
        if self.should_tb :
            pass #TODO implements it.
        if self.should_ping :
            ping_server_list = Pingsites.objects.all()
            for ping_server in ping_server_list :
                pass #TODO implements it.

    delete = delete_for_related


class Comment(models.Model) :
    entry = models.ForeignKey(Entry)
    author = models.CharField(_('Commentator'), max_length=50)
    url = models.URLField(_('URL'), blank=True)
    body = models.TextField(_('Body'), blank=False)
    create_date = models.DateTimeField(_('Comment date'), auto_now_add=True)

    def _get_entry_author(self):
        return self.entry.author
    entry_author = property(_get_entry_author)

    def save(self):
        if not self.id > 0:
            e = self.entry
            e.comment_count = e.comment_count + 1
            e.save()
        super(Comment, self).save()

    def delete(self):
        entry = self.entry
        entry.comment_count -= 1
        entry.save()
        super(Comment, self).delete()

class Trackback(models.Model) :
    entry = models.ForeignKey(Entry)
    blog_name = models.CharField(_('Blog name'), max_length=200, blank=True)
    url = models.URLField(_('URL'), blank=False, verify_exists=False)
    excerpt = models.TextField(_('Excerpt'), blank=False)
    create_date = models.DateTimeField(_('Trackback date'), auto_now_add=True)

    def save(self):
        if not self.id > 0:
            e = self.entry
            e.trackback_count = e.trackback_count + 1
            e.save()
        super(Trackback, self).save()

    def delete(self):
        entry = self.entry
        entry.trackback_count -= 1
        entry.save()
        super(Trackback, self).delete()

class Pingsites(models.Model) :
    create_date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=50, blank=False)
    ping_url = models.URLField(_('URL'), blank=False, verify_exists=False)

class RelatedFile(models.Model, RelatedModelBase):
    title = models.CharField(_('title'), max_length=100, blank=False)
    description = models.CharField(_('description'), max_length=200, blank=True)
    file = models.FileField(_('file'), upload_to=os.path.join('related','stuff'))

    delete = delete_for_related

    def as_list(self):
        return '<a href="%s"/>%s</a> (%s)' % (self.get_absolute_url(), self.title, self.description, )

    def __unicode__(self) :
        return self.title

    def get_absolute_url(self):
        return self.get_file_url()
    absolute_url = property(get_absolute_url)

    def _file_name(self):
        return os.path.split(self.file)[1]
    file_name = property(_file_name)


class RelatedImage(models.Model, RelatedModelBase):
    image        = models.ImageField(_('Image'), width_field='image_width', height_field='image_height', upload_to='related_images/%Y/%m/%d/')
    title        = models.CharField(_('Caption'), max_length=80)
    image_width  = models.IntegerField(_('Width'), blank=True, null=True)
    image_height = models.IntegerField(_('Height'), blank=True, null=True)
    description  = models.TextField(_('Description'), blank=True)
    create_date  = models.DateField(_('Create Date'), auto_now_add=True)

    inline = True
    t = 'related_image.html'
    delete = delete_for_related
    def as_list(self):
        return '<img src="%s" width="50" height="50" />%s' % ( self.image_url, self.description,)

    def _image_url(self):
        return '%s/%s' % (settings.MEDIA_URL,  self.image)
    image_url = property(_image_url)

    def __unicode__(self):
        return self.title

