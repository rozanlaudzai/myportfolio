from django import forms
from django.db import transaction

from .models import Award, Experience, Skill

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

class ExperienceForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        help_text='Separate skills with commas, e.g. Python, Django, Project Management. New skills are added automatically.',
        widget=forms.TextInput(attrs={'placeholder': 'Python, Django, Project Management'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.instance._state.adding:
            self.initial['skills'] = ', '.join(self.instance.skills.values_list('name', flat=True))

    def clean_skills(self):
        names = []
        seen = set()
        for value in self.cleaned_data['skills'].split(','):
            name = ' '.join(value.split())
            if not name:
                continue
            if len(name) > 255:
                raise forms.ValidationError('Each skill name must be 255 characters or fewer.')
            if name.casefold() not in seen:
                names.append(name)
                seen.add(name.casefold())
        return names

    @transaction.atomic
    def _save_m2m(self):
        skills = []
        for name in self.cleaned_data['skills']:
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill, _ = Skill.objects.get_or_create(name=name)
            skills.append(skill)
        self.instance.skills.set(skills)

    @transaction.atomic
    def save(self, commit=True):
        return super().save(commit=commit)

    class Meta:
        model = Experience
        fields = ['title', 'company_name', 'company_logo', 'description',
                  'started_at', 'ended_at', 'skills']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'started_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'ended_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        help_texts = {
            'ended_at': 'Leave blank for an ongoing experience.',
            'company_logo': 'Optional URL for the company logo.',
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('started_at'), cleaned.get('ended_at')
        if start and end and end < start:
            self.add_error('ended_at', 'End date cannot be before start date.')
        return cleaned
