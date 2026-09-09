from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Experience

class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title='Asisten Dosen PBP',
            description='Membantu mahasiswa memahami pengembangan web.',
            category='part-time',
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse('main:index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/index.html')
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:index")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get('/this-page-does-not-exist')

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), 'Asisten Dosen PBP')
        self.assertEqual(self.experience.category, 'part-time')
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse('main:show_experience'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/experience.html')
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, 'Part-Time')
        self.assertContains(response, 'On Going')
        self.assertContains(response, f'href="{reverse("main:index")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()

        response = self.client.get(reverse('main:show_experience'))

        self.assertContains(response, 'No experience added.')

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()

        response = self.client.get(reverse('main:show_experience'))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, 'Ended')
        self.assertNotContains(response, 'On Going')
