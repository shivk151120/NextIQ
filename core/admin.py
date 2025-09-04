from django.contrib import admin
from .models import User, Phrase, Attempt, BeltAward, Example, SiteSetting, ParentLink

admin.site.register(User)
admin.site.register(Phrase)
admin.site.register(Attempt)
admin.site.register(BeltAward)
admin.site.register(Example)
admin.site.register(SiteSetting)
admin.site.register(ParentLink)
