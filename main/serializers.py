from django.db import transaction
from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.request import HttpRequest

from .models import Award, Experience, Skill

class AwardSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = [
            'id',
            'title',
            'issuer',
            'description',
            'awarded_at',
            'star_count',
            'is_starred',
            'starred_by_names',
        ]
        read_only_fields = ['id']

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Title cannot be empty.')
        return value

    def validate_issuer(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Issuer cannot be empty.')
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Description cannot be empty.')
        return value

    def get_star_count(self, obj: Award) -> int:
        return obj.starred_by.count()
    
    def get_is_starred(self, obj: Award) -> bool:
        request: HttpRequest = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj: Award) -> str:
        return ', '.join(user.username for user in obj.starred_by.all())
        


class SkillNamesField(serializers.ListField):
    def to_representation(self, value):
        return [skill.name for skill in value.all()]


class ExperienceSerializer(serializers.ModelSerializer):
    """Keep the existing skill vocabulary; expose no user account data."""

    skills = SkillNamesField(
        child=serializers.CharField(max_length=255), required=False,
    )
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = [
            'id', 'title', 'company_name', 'company_logo', 'description',
            'started_at', 'ended_at', 'skills', 'star_count', 'is_starred',
        ]
        read_only_fields = ['id']

    def _clean_text(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('This field cannot contain only HTML tags or whitespace.')
        return value

    def validate_title(self, value):
        return self._clean_text(value)

    def validate_company_name(self, value):
        return self._clean_text(value)

    def validate_description(self, value):
        return self._clean_text(value)

    def validate_skills(self, values):
        names, seen = [], set()
        for value in values:
            name = ' '.join(self._clean_text(value).split())
            if name.casefold() not in seen:
                seen.add(name.casefold())
                names.append(name)
        return names

    def validate(self, attrs):
        start = attrs.get('started_at', getattr(self.instance, 'started_at', None))
        end = attrs.get('ended_at', getattr(self.instance, 'ended_at', None))
        if start and end and end < start:
            raise serializers.ValidationError({'ended_at': 'End date cannot be before start date.'})
        return attrs

    def _set_skills(self, instance, names):
        skills = []
        for name in names:
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill, _ = Skill.objects.get_or_create(name=name)
            skills.append(skill)
        instance.skills.set(skills)

    @transaction.atomic
    def create(self, validated_data):
        names = validated_data.pop('skills', [])
        instance = super().create(validated_data)
        self._set_skills(instance, names)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        names = validated_data.pop('skills', None)
        instance = super().update(instance, validated_data)
        if names is not None:
            self._set_skills(instance, names)
        return instance

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated
                    and any(user.pk == request.user.pk for user in obj.starred_by.all()))
