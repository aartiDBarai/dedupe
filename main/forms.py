from django import forms

class FileForm(forms.Form):
    file_name = forms.CharField(max_length=5000)
    file = forms.FileField()
