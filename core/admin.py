from django.contrib import admin
from .models import User, Phrase, Attempt, BeltAward, Example, SiteSetting, ParentLink

admin.site.register(User)
admin.site.register(Phrase)
admin.site.register(Attempt)
admin.site.register(BeltAward)
admin.site.register(Example)
admin.site.register(ParentLink)

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('org_name', 'abn', 'contact_email', 'phone')
    fields = ('org_name', 'abn', 'contact_email', 'phone', 'footer_note', 'banner_image', 'banner_text')
