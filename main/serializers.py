from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.request import HttpRequest

from .models import Award

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
        
