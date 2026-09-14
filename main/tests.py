from datetime import date
from django.test import TestCase
from django.urls import reverse

from .models import Experience, Skill

class MainTest(TestCase):
    def test_main_url_is_accessible(self):
        response = self.client.get(reverse('main:index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/index.html')
        self.assertContains(response, f'href="{reverse("main:index")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get('/this-page-does-not-exist')

        self.assertEqual(response.status_code, 404)

class ExperienceTest(TestCase):
    def setUp(self):
        self.django = Skill.objects.create(
            name='Django'
        )
        self.experience = Experience.objects.create(
            title='Asisten Dosen PBP',
            company_name='Universitas Indonesia',
            company_logo='img/pelihara-logo.webp',
            description='Membantu mahasiswa memahami pengembangan web.',
            started_at=date(2026, 8, 1),
        )
        self.experience.skills.add(self.django)

    def test_experience_model(self):
        self.assertEqual(
            str(self.experience),
            'Asisten Dosen PBP at Universitas Indonesia',
        )
        self.assertQuerySetEqual(self.experience.skills.all(), [self.django])
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_is_not_shown_on_profile(self):
        response = self.client.get(reverse('main:index'))

        self.assertNotContains(response, self.experience.title)

    def test_experience_page(self):
        response = self.client.get(reverse('main:show_experience'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/experience.html')
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, self.experience.company_name)
        self.assertContains(response, '<li>Django</li>', html=True)
        self.assertContains(response, '<time>Aug 2026</time>', html=True)
        self.assertContains(response, '<time>Present</time>', html=True)
        self.assertContains(response, f'href="{reverse("main:index")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()

        response = self.client.get(reverse('main:show_experience'))

        self.assertContains(response, 'No experience added yet.')

    def test_completed_experience(self):
        self.experience.ended_at = date(2026, 12, 1)
        self.experience.save()
        self.experience.refresh_from_db()

        response = self.client.get(reverse('main:show_experience'))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, '<time>Aug 2026</time>', html=True)
        self.assertContains(response, '<time>Dec 2026</time>', html=True)
        self.assertNotContains(response, '<time>Present</time>', html=True)
