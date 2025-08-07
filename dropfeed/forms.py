from django import forms
from .models import Recording


class RecordingForm(forms.ModelForm):
    class Meta:
        model = Recording
        fields = ['name', 'description', 'audio_file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recording name (required)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (optional)'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/mpeg,.mp3'
            })
        }
