from django import forms

class URLForm(forms.Form):
    url_field = forms.URLField(label='Введіть URL', max_length=255)
