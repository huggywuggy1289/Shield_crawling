from django import forms

class URLForm(forms.Form):
    url = forms.URLField(label='Website URL', max_length=200)
