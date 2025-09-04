from django import forms
from .models import Phrase, Example, SiteSetting, ParentLink, User

class PhraseForm(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = ["text", "audio", "acara_code"]

class ExampleForm(forms.ModelForm):
    class Meta:
        model = Example
        fields = ["title", "image", "summary", "content", "link_phrase", "external_url"]

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ["org_name", "abn", "contact_email", "phone", "footer_note", "banner_image", "banner_text"]

class ParentLinkForm(forms.ModelForm):
    class Meta:
        model = ParentLink
        fields = ["student", "parent"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = User.objects.filter(role="student")
        self.fields["parent"].queryset = User.objects.filter(role="parent")
