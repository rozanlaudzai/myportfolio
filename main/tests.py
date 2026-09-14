from datetime import date
from django.test import TestCase
from django.urls import reverse

from .models import Award, Experience, Skill

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

class AwardTest(TestCase):
    def setUp(self):
        self.award = Award.objects.create(
            title='Juara Hackathon',
            issuer='Universitas Indonesia',
            description='Membangun aplikasi untuk mahasiswa.',
            awarded_at=date(2026, 8, 1),
        )

    def test_award_model(self):
        self.assertEqual(
            str(self.award),
            'Juara Hackathon - Universitas Indonesia',
        )

    def test_awards_page(self):
        response = self.client.get(reverse('main:show_awards'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/awards.html')
        self.assertQuerySetEqual(response.context['award_list'], [self.award])
        self.assertContains(response, self.award.title)
        self.assertContains(response, self.award.issuer)
        self.assertContains(response, self.award.description)
        self.assertContains(
            response,
            '<time class="award-date" datetime="2026-08-01">Aug 2026</time>',
            html=True,
        )
        self.assertNotContains(response, 'No awards added yet.')
        self.assertContains(response, f'href="{reverse("main:index")}"')

    def test_awards_ordered_by_newest_date_then_title(self):
        older_award = Award.objects.create(
            title='Academic Award',
            issuer='Universitas Indonesia',
            description='Academic achievement.',
            awarded_at=date(2025, 8, 1),
        )
        same_date_award = Award.objects.create(
            title='Best Project',
            issuer='Universitas Indonesia',
            description='Outstanding project.',
            awarded_at=self.award.awarded_at,
        )

        response = self.client.get(reverse('main:show_awards'))

        expected = [same_date_award, self.award, older_award]
        self.assertQuerySetEqual(Award.objects.all(), expected)
        self.assertQuerySetEqual(response.context['award_list'], expected)
        content = response.content.decode()
        positions = [content.index(f'id="award-{award.id}"') for award in expected]
        self.assertEqual(positions, sorted(positions))

    def test_empty_awards_page(self):
        Award.objects.all().delete()

        response = self.client.get(reverse('main:show_awards'))

        self.assertTemplateUsed(response, 'main/awards.html')
        self.assertQuerySetEqual(response.context['award_list'], [])
        self.assertContains(response, 'No awards added yet.')

    def test_award_description_preserves_line_breaks_and_escapes_html(self):
        self.award.description = 'First line\n<script>alert("test")</script>'
        self.award.save()

        response = self.client.get(reverse('main:show_awards'))

        self.assertContains(
            response,
            'First line<br>&lt;script&gt;alert(&quot;test&quot;)&lt;/script&gt;',
        )
        self.assertNotContains(response, '<script>')
