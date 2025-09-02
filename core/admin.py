from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Phrase, Attempt, Badge

# Register each model so it shows up in admin
admin.site.register(User)
admin.site.register(Phrase)
admin.site.register(Attempt)
admin.site.register(Badge)
