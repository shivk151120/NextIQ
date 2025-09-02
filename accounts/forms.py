from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User

ROLE_CHOICES = [
    ('student', 'Student'),
    ('parent', 'Parent'),
    ('teacher', 'Teacher'),
]

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
