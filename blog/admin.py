from django.contrib import admin
from models import RelatedItem, Relatable, Tag, Entry, Comment, Trackback, RelatedFile, RelatedImage, Pingsites
from django.utils.translation import gettext as _

class RelatedItemOption(admin.ModelAdmin):
    list_display = ('content_type', 'object_id', 'related_content_type', 'related_object_id', 'pub_date')
    ordering = ("-pub_date",)
    verbose_name = _('Related Item')
    verbose_name_plural = _('Releted Items')

class RelatableOption(admin.ModelAdmin):
    ordering = ("-id",)
    verbose_name = _('Relatable Model')
    verbose_name_plural = _('Relatable Models')

class TagOption(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
    verbose_name = _('Tag')
    verbose_name_plural = _('Tags')

class EntryOption(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('title','author',)}
    filter_horizontal = ('tags', )
    ordering = ['-create_date']
    verbose_name = _('Entry')
    verbose_name_plural = _('Entries')
    list_display = ('title', 'create_date', 'author', 'comment_count', 'trackback_count',)
    list_filter = ('create_date','visible','tags',)
    date_hierarchy = 'create_date'
    search_fields = ('title', 'body', 'author',)
    fieldsets = (
        (None, {
            'fields': (('title', 'author',), 'slug', 'tags', 'visible', 'summary', 'body', 'ping_now', )
        }),
        (_('Comment options'), {
            'classes': 'collapse',
            'fields' : ('riddle', 'answer',)
        }),
        (_('Trackback options'), {
            'classes': 'collapse',
            'fields' : ('trackback_now', 'trackbacked_sites',)
        }),
    )

class CommentOption(admin.ModelAdmin):
    list_display = ('create_date', 'author', 'entry_author')
    ordering = ('-create_date',)
    verbose_name = _('Comment')
    verbose_name_plural = _('Comments')

class TrackbackOption(admin.ModelAdmin):
    list_display = ('create_date', 'blog_name')
    ordering = ('-create_date',)
    verbose_name = _('Trackback')
    verbose_name_plural = _('Trackbacks')

class PingsitesOption(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('create_date', 'name',)
    verbose_name = _('Ping site')
    verbose_name_plural = _('Ping sites')

class RelatedFileOption(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title', 'description', 'file')
    verbose_name = _('File')
    verbose_name_plural = _('Files')

class RelatedImageOption(admin.ModelAdmin):
    ordering = ['-create_date']
    list_display = ('title', 'create_date', )
    search_fields = ('title', 'description', )
    verbose_name = _('Image')
    verbose_name_plural = _('Images')

admin.site.register(RelatedImage, RelatedImageOption)
admin.site.register(RelatedFile, RelatedFileOption)
admin.site.register(Pingsites, PingsitesOption)
admin.site.register(Trackback, TrackbackOption)
admin.site.register(RelatedItem, RelatedItemOption)
admin.site.register(Relatable, RelatableOption)
admin.site.register(Tag, TagOption)
admin.site.register(Entry, EntryOption)
admin.site.register(Comment, CommentOption)
