from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Custom User with role
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return self.username


# Content (curriculum)
class Phrase(models.Model):
    text = models.CharField(max_length=255)
    audio = models.FileField(upload_to="audio/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phrases")

    def __str__(self):
        return self.text


# Student Attempts (assessment)
class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="attempts")
    is_correct = models.BooleanField(default=False)
    time_taken = models.IntegerField(default=0)  # in seconds
    attempt_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.phrase.text[:20]}"


# Gamification
class Badge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    name = models.CharField(max_length=100)
    earned_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"


# Comments
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user: settings.AUTH_USER_MODEL = self.user
        phrase: Phrase = self.phrase
        phrase_text = phrase.text[:20] if phrase else "Deleted Phrase"
        username = user.username if user else "Deleted User"
        return f"{username} - {phrase_text}"


# Likes
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'phrase')

    def __str__(self):
        user: settings.AUTH_USER_MODEL = self.user
        phrase: Phrase = self.phrase
        phrase_text = phrase.text[:20] if phrase else "Deleted Phrase"
        username = user.username if user else "Deleted User"
        return f"{username} liked '{phrase_text}'"
