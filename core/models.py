from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# -----------------------------
# Custom User with role
# -----------------------------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    # New field to link a parent to a student
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )

    def __str__(self):
        return self.username


# -----------------------------
# Site-wide editable footer + banner
# -----------------------------
class SiteSetting(models.Model):
    org_name = models.CharField(max_length=200, blank=True, default="Alloneword")
    abn = models.CharField(max_length=50, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    footer_note = models.TextField(blank=True, default="")
    banner_image = models.ImageField(upload_to="banners/", null=True, blank=True)
    banner_text = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    @classmethod
    def get(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj


# -----------------------------
# Content (curriculum)
# -----------------------------
class Phrase(models.Model):
    text = models.CharField(max_length=255)
    audio = models.FileField(upload_to="audio/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phrases")
    acara_code = models.CharField(max_length=50, blank=True, default="")  # optional curriculum tag

    def __str__(self):
        return self.text


# -----------------------------
# Student Attempts (assessment)
# -----------------------------
class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    time_taken = models.IntegerField(default=0)  # seconds
    attempt_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.phrase.text[:20]}"


# -----------------------------
# “Belts” Gamification
# -----------------------------
BELTS = [
    (0, "White"),
    (5, "Yellow"),
    (10, "Green"),
    (20, "Blue"),
    (35, "Brown"),
    (50, "Black"),
]

def belt_for_correct(correct_count: int) -> str:
    current = "White"
    for threshold, name in BELTS:
        if correct_count >= threshold:
            current = name
    return current

class BeltAward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="belt_awards")
    name = models.CharField(max_length=50)  # White/Yellow/Green/...
    awarded_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user.username} - {self.name} Belt"


# -----------------------------
# Parent ↔ Student linking
# -----------------------------
class ParentLink(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="linked_parents")
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="linked_children")

    class Meta:
        unique_together = ('student', 'parent')

    def __str__(self):
        return f"{self.student.username} ↔ {self.parent.username}"


# -----------------------------
# Comments / Likes
# -----------------------------
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        phrase_text = self.phrase.text[:20] if self.phrase else "Deleted Phrase"
        username = self.user.username if self.user else "Deleted User"
        return f"{username} - {phrase_text}"


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'phrase')

    def __str__(self):
        phrase_text = self.phrase.text[:20] if self.phrase else "Deleted Phrase"
        username = self.user.username if self.user else "Deleted User"
        return f"{username} liked '{phrase_text}'"


# -----------------------------
# Examples hub (cards → detail)
# -----------------------------
class Example(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="examples/", null=True, blank=True)
    summary = models.CharField(max_length=300, blank=True, default="")
    content = models.TextField(blank=True, default="")           # essay/instructions
    link_phrase = models.ForeignKey(Phrase, null=True, blank=True, on_delete=models.SET_NULL)
    external_url = models.URLField(blank=True, default="")       # optional

    def __str__(self):
        return self.title
