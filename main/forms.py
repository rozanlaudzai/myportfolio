from django import forms

from .models import Award

class AwardForm(forms.ModelForm):
    class Meta:
        model = Award

        fields = [
            'title',
            'issuer',
            'description',
            'awarded_at',
        ]

        labels = {
            'title': 'Award Title',
            'issuer': 'Award Issuer',
            'description': 'Award Description',
            'awarded_at': 'Date Awarded',
        }

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': labels.get('title', ''),
                    'maxlength': 255,
                }
            ),
            'issuer': forms.TextInput(
                attrs={
                    'placeholder': labels.get('issuer', ''),
                    'maxlength': 255,
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'placeholder': labels.get('description', ''),
                    'rows': 3,
                }
            ),
            'awarded_at': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                }
            ),
        }
