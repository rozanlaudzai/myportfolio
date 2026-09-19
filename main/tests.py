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

class AwardEditTest(TestCase):
    def setUp(self):
        self.award = Award.objects.create(
            title='Original Award',
            issuer='Original Issuer',
            description='First line\nSecond line',
            awarded_at=date(2026, 8, 1),
        )
        self.url = reverse('main:edit_award', args=[self.award.pk])
        self.data = {
            'title': 'Updated Award',
            'issuer': 'Updated Issuer',
            'description': 'Updated description\nAnother line',
            'awarded_at': '2026-09-19',
        }

    def test_edit_link_on_awards_page(self):
        response = self.client.get(reverse('main:show_awards'))

        self.assertContains(response, f'href="{self.url}"')

    def test_edit_form_is_prefilled(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/award-form.html')
        self.assertContains(response, 'Edit Award')
        self.assertContains(response, 'Save Changes')
        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, 'value="2026-08-01"')
        form = response.context['form']
        self.assertFalse(form.is_bound)
        for field in ('title', 'issuer', 'description', 'awarded_at'):
            self.assertEqual(form.initial[field], getattr(self.award, field))
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Original Award')

    def test_valid_edit_updates_existing_award(self):
        other = Award.objects.create(
            title='Other Award', issuer='Other Issuer',
            description='Unchanged', awarded_at=date(2025, 1, 1),
        )
        response = self.client.post(self.url, self.data, follow=True)

        self.assertRedirects(response, reverse('main:show_awards'))
        self.assertContains(response, 'Award successfully updated!')
        self.award.refresh_from_db()
        for field in ('title', 'issuer', 'description'):
            self.assertEqual(getattr(self.award, field), self.data[field])
        self.assertEqual(self.award.awarded_at, date(2026, 9, 19))
        self.assertEqual(Award.objects.count(), 2)
        other.refresh_from_db()
        self.assertEqual(other.title, 'Other Award')

    def test_invalid_edit_does_not_change_award(self):
        for invalid_data in ({}, {**self.data, 'title': ''},
                             {**self.data, 'awarded_at': 'not-a-date'}):
            with self.subTest(data=invalid_data):
                response = self.client.post(self.url, invalid_data)

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].is_bound)
                self.assertTrue(response.context['form'].errors)
                self.assertContains(response, 'form-error')
                self.assertContains(response, f'action="{self.url}"')
                self.award.refresh_from_db()
                self.assertEqual(self.award.title, 'Original Award')
                self.assertEqual(self.award.issuer, 'Original Issuer')
                self.assertEqual(self.award.description, 'First line\nSecond line')
                self.assertEqual(self.award.awarded_at, date(2026, 8, 1))
                self.assertEqual(Award.objects.count(), 1)
        self.assertEqual(response.context['form']['title'].value(), 'Updated Award')

    def test_missing_award_returns_404(self):
        self.award.delete()

        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 404)

    def test_unsupported_method_returns_405(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertTrue(Award.objects.filter(pk=self.award.pk).exists())

    def test_edit_requires_csrf_token(self):
        from django.test import Client

        response = Client(enforce_csrf_checks=True).post(self.url, self.data)

        self.assertEqual(response.status_code, 403)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Original Award')

    def test_shared_form_still_creates_awards(self):
        url = reverse('main:create_award')
        response = self.client.get(url)

        self.assertContains(response, 'Add New Award')
        self.assertContains(response, f'action="{url}"')
        response = self.client.post(url, self.data)

        self.assertRedirects(response, reverse('main:show_awards'))
        self.assertEqual(Award.objects.count(), 2)
        self.assertTrue(Award.objects.filter(title='Updated Award').exists())

class ExperienceCrudTest(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(name='Python')
        self.other_skill = Skill.objects.create(name='Django')
        self.data = {
            'title': 'Developer', 'company_name': 'Example',
            'company_logo': 'https://example.com/logo.png',
            'description': 'Built applications.', 'started_at': '2026-01-01',
            'ended_at': '', 'skills': 'Python, Django',
        }
        self.experience = Experience.objects.create(
            title='Original', company_name='Example', description='Original description',
            started_at=date(2025, 1, 1),
        )
        self.experience.skills.add(self.skill)

    def test_create_with_multiple_skills(self):
        url = reverse('main:create_experience')
        response = self.client.get(url)
        self.assertContains(response, 'Python')
        self.assertContains(response, 'Django')
        response = self.client.post(url, self.data)
        self.assertRedirects(response, reverse('main:show_experience'))
        created = Experience.objects.get(title='Developer')
        self.assertSetEqual(set(created.skills.all()), {self.skill, self.other_skill})
        self.assertTrue(created.is_ongoing)
        response = self.client.get(reverse('main:show_experience'))
        self.assertContains(response, 'src="https://example.com/logo.png"')

    def test_create_without_optional_fields(self):
        data = {**self.data, 'skills': '', 'company_logo': ''}
        response = self.client.post(reverse('main:create_experience'), data)
        self.assertRedirects(response, reverse('main:show_experience'))
        self.assertFalse(Experience.objects.get(title='Developer').skills.exists())

    def test_edit_prefills_and_replaces_skills(self):
        url = reverse('main:edit_experience', args=[self.experience.pk])
        response = self.client.get(url)
        self.assertContains(response, 'value="2025-01-01"')
        self.assertEqual(response.context['form'].initial['skills'], 'Python')
        response = self.client.post(url, {**self.data, 'skills': 'Django', 'ended_at': '2026-09-01'})
        self.assertRedirects(response, reverse('main:show_experience'))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, 'Developer')
        self.assertFalse(self.experience.is_ongoing)
        self.assertQuerySetEqual(self.experience.skills.all(), [self.other_skill])
        self.assertEqual(Experience.objects.count(), 1)
        self.client.post(url, {**self.data, 'skills': ''})
        self.assertFalse(self.experience.skills.exists())

    def test_invalid_data_preserves_record_and_skills(self):
        url = reverse('main:edit_experience', args=[self.experience.pk])
        for data in ({}, {**self.data, 'ended_at': '2024-01-01'},
                     {**self.data, 'skills': 'x' * 256},
                     {**self.data, 'company_logo': 'invalid'}):
            with self.subTest(data=data):
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.experience.refresh_from_db()
                self.assertEqual(self.experience.title, 'Original')
                self.assertQuerySetEqual(self.experience.skills.all(), [self.skill])
        response = self.client.post(reverse('main:create_experience'), {})
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Experience.objects.count(), 1)

    def test_delete_confirmation_then_post(self):
        url = reverse('main:delete_experience', args=[self.experience.pk])
        self.assertContains(self.client.get(url), 'Delete Experience?')
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())
        self.assertRedirects(self.client.post(url), reverse('main:show_experience'))
        self.assertFalse(Experience.objects.exists())
        self.assertEqual(Skill.objects.count(), 2)

    def test_search_and_missing_records(self):
        response = self.client.get(reverse('main:show_experience'), {'title': ' ORIGINAL '})
        self.assertContains(response, self.experience.title)
        response = self.client.get(reverse('main:show_experience'), {'title': 'missing'})
        self.assertContains(response, 'No experiences found.')
        pk = self.experience.pk
        self.experience.delete()
        for action in ('edit_experience', 'delete_experience'):
            url = reverse(f'main:{action}', args=[pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.data).status_code, 404)

    def test_typed_skills_reuse_existing_names_and_create_new_ones(self):
        response = self.client.post(reverse('main:create_experience'), {
            **self.data, 'skills': ' python, PYTHON, Django, Go, go, Project   Management, , ',
        })
        self.assertRedirects(response, reverse('main:show_experience'))
        created = Experience.objects.get(title='Developer')
        self.assertSetEqual(set(created.skills.values_list('name', flat=True)),
                            {'Python', 'Django', 'Go', 'Project Management'})
        self.assertEqual(Skill.objects.count(), 4)
        self.assertTrue(created.skills.filter(pk=self.skill.pk).exists())

    def test_invalid_experience_does_not_create_skills(self):
        response = self.client.post(reverse('main:create_experience'), {
            **self.data, 'title': '', 'skills': 'New Skill',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="New Skill"')
        self.assertFalse(Skill.objects.filter(name='New Skill').exists())
        self.assertEqual(Experience.objects.count(), 1)

    def test_edit_adds_new_skills_without_changing_other_experiences(self):
        url = reverse('main:edit_experience', args=[self.experience.pk])
        self.client.post(reverse('main:create_experience'), self.data)
        response = self.client.post(url, {**self.data, 'skills': 'Rust'})
        self.assertRedirects(response, reverse('main:show_experience'))
        self.assertEqual(list(self.experience.skills.values_list('name', flat=True)), ['Rust'])
        other = Experience.objects.exclude(pk=self.experience.pk).get()
        self.assertSetEqual(set(other.skills.all()), {self.skill, self.other_skill})
        self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_skill_form_supports_deferred_save(self):
        from .forms import ExperienceForm
        form = ExperienceForm(data={**self.data, 'skills': 'Rust'})
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save(commit=False)
        self.assertFalse(Skill.objects.filter(name='Rust').exists())
        instance.save()
        form.save_m2m()
        self.assertEqual(list(instance.skills.values_list('name', flat=True)), ['Rust'])

    def test_no_separate_skill_section(self):
        response = self.client.get(reverse('main:show_experience'))
        self.assertNotContains(response, 'href="/skills/"')
        self.assertEqual(self.client.get('/skills/').status_code, 404)

    def test_mutations_require_csrf_and_reject_unsupported_methods(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        for url in (reverse('main:create_experience'),
                    reverse('main:edit_experience', args=[self.experience.pk]),
                    reverse('main:delete_experience', args=[self.experience.pk])):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {}).status_code, 403)
                self.assertEqual(self.client.delete(url).status_code, 405)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())
