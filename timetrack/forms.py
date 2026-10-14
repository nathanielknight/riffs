from django import forms

from .models import Interval

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format=DATETIME_FORMAT, attrs={"step": 300}, **kwargs)


class IntervalForm(forms.ModelForm):
    label_suffix = ""

    class Meta:
        model = Interval
        fields = ["project", "note", "start", "end"]
        widgets = {
            "project": forms.TextInput(attrs={"list": "projects"}),
            "start": DateTimeInput(),
            "end": DateTimeInput(),
        }
        help_texts = {
            "end": "Leave blank if you're still working.",
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start"), cleaned.get("end")
        if start and end and end < start:
            self.add_error("end", "End must be after start.")
        return cleaned
