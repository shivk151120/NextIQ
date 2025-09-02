from django import forms
from .models import Phrase

class PhraseForm(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = ['text', 'audio']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phrase text'}),
        }
