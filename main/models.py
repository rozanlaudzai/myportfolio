from django.db import models
import uuid

class Skill(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Experience(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    company_logo = models.URLField(blank=True)
    description = models.TextField()
    started_at = models.DateField()
    ended_at = models.DateField(blank=True, null=True)
    skills = models.ManyToManyField(
        Skill,
        related_name='experiences',
        blank=True,
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.title} at {self.company_name}'

    @property
    def is_ongoing(self):
        return self.ended_at is None
