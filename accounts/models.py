from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models

class Badge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounts_badges'  # unique name
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
