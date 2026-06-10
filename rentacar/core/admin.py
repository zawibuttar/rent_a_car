from django.contrib import admin
from .models import SocialLink


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display  = ('platform', 'url', 'is_active')
    list_editable = ('url',)
    ordering      = ('platform',)

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean     = True
    is_active.short_description = 'Active'
