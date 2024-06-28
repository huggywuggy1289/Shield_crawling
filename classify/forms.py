from django import forms
from .models import Whitelist


class URLForm(forms.Form):
    url = forms.URLField(label='URL', max_length=200)

class RegisterForm(forms.Form):
    url = forms.URLField(label='URL', max_length=200)
    category = forms.ChoiceField(label='Category', choices=[
        ('정상', '정상'),
        ('도박사이트', '도박사이트'),
        ('성인사이트', '성인사이트'),
        ('불법저작물배포사이트', '불법저작물배포사이트')
    ])


class WhitelistForm(forms.ModelForm):
    class Meta:
        model = Whitelist
        fields = ['url']
