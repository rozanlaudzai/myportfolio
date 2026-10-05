from datetime import date
from django.test import (
    Client,
    TestCase,
)
from django.urls import reverse
from django.contrib.auth.models import (
    Group,
    User,
)

from .models import (
    Award,
    Experience,
    Skill,
)

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
        self.assertContains(response, 'id="experience-list"')
        self.assertContains(response, 'js/experience.js')
        self.assertNotContains(response, self.experience.title)
        data = self.client.get(reverse('main:get_experience_json')).json()[0]['fields']
        self.assertEqual(data['title'], self.experience.title)
        self.assertEqual(data['description'], self.experience.description)
        self.assertEqual(data['company_name'], self.experience.company_name)
        self.assertEqual(data['skill_names'], ['Django'])
        self.assertEqual(data['started_at'], '2026-08-01')
        self.assertIsNone(data['ended_at'])

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse('main:show_experience'))
        self.assertContains(response, 'id="experience-empty"')
        self.assertEqual(self.client.get(reverse('main:get_experience_json')).json(), [])

    def test_completed_experience(self):
        self.experience.ended_at = date(2026, 12, 1)
        self.experience.save()
        self.assertFalse(self.experience.is_ongoing)
        data = self.client.get(reverse('main:get_experience_json')).json()[0]['fields']
        self.assertEqual(data['started_at'], '2026-08-01')
        self.assertEqual(data['ended_at'], '2026-12-01')


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
        self.assertContains(response, '<ol id="list" class="awards-list hide" role="list"></ol>', html=True)
        self.assertNotContains(response, self.award.title)
        data = self.client.get(reverse('main:get_awards_json')).json()
        self.assertEqual(data, [{
            'pk': str(self.award.pk),
            'fields': {
                'title': self.award.title, 'issuer': self.award.issuer,
                'description': self.award.description, 'awarded_at': '2026-08-01',
                'star_count': 0, 'is_starred': False, 'starred_by_names': '',
            },
        }])
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

        response = self.client.get(reverse('main:get_awards_json'))

        expected = [same_date_award, self.award, older_award]
        self.assertQuerySetEqual(Award.objects.all(), expected)
        self.assertEqual([item['pk'] for item in response.json()],
                         [str(award.pk) for award in expected])

    def test_empty_awards_page(self):
        Award.objects.all().delete()
        response = self.client.get(reverse('main:show_awards'))
        self.assertTemplateUsed(response, 'main/awards.html')
        self.assertContains(response, 'No awards added or found yet.')
        self.assertEqual(self.client.get(reverse('main:get_awards_json')).json(), [])

    def test_award_description_is_returned_as_json_without_embedding_in_page(self):
        self.award.description = 'First line\n<script>alert("test")</script>'
        self.award.save()
        response = self.client.get(reverse('main:get_awards_json'))
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()[0]['fields']['description'], self.award.description)
        page = self.client.get(reverse('main:show_awards'))
        self.assertNotContains(page, self.award.description)


class AwardEditTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', is_superuser=True)
        self.client.force_login(self.owner)
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

    def test_awards_page_enables_owner_editing(self):
        response = self.client.get(reverse('main:show_awards'))
        self.assertTrue(response.context['user'].is_superuser)
        self.assertEqual(self.client.get(self.url).status_code, 200)

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

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(self.url, self.data)

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
        self.owner = User.objects.create_user(username='owner', is_superuser=True)
        self.client.force_login(self.owner)
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
        data = self.client.get(reverse('main:get_experience_json')).json()
        self.assertEqual(data[0]['fields']['company_logo'], 'https://example.com/logo.png')

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
        self.assertEqual(response.context['title_query'], 'ORIGINAL')
        data = self.client.get(reverse('main:get_experience_json'), {'title': ' ORIGINAL '}).json()
        self.assertEqual([item['pk'] for item in data], [str(self.experience.pk)])
        self.assertEqual(self.client.get(reverse('main:get_experience_json'), {'title': 'missing'}).json(), [])
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
        client.force_login(self.owner)
        for url in (reverse('main:create_experience'),
                    reverse('main:edit_experience', args=[self.experience.pk]),
                    reverse('main:delete_experience', args=[self.experience.pk])):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {}).status_code, 403)
                self.assertEqual(self.client.delete(url).status_code, 405)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())


class ExperienceJsonTest(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(name='Django')
        self.experience = Experience.objects.create(
            title='Developer', company_name='Example',
            description='Built applications.', started_at=date(2026, 1, 1),
        )
        self.experience.skills.add(self.skill)
        self.url = reverse('main:get_experience_json')

    def test_json_contains_fields_and_skill_ids(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), [{
            'model': 'main.experience',
            'pk': str(self.experience.pk),
            'fields': {
                'title': 'Developer', 'company_name': 'Example',
                'company_logo': '', 'description': 'Built applications.',
                'started_at': '2026-01-01', 'ended_at': None,
                'skills': [str(self.skill.pk)],
                'skill_names': ['Django'],
            },
        }])

    def test_json_ordering_and_title_filter(self):
        newer = Experience.objects.create(
            title='Designer', company_name='Example', description='Design work.',
            started_at=date(2026, 9, 1), ended_at=date(2026, 9, 20),
        )
        self.assertEqual([item['pk'] for item in self.client.get(self.url).json()],
                         [str(newer.pk), str(self.experience.pk)])
        response = self.client.get(self.url, {'title': ' DEVELOP '})
        self.assertEqual([item['pk'] for item in response.json()], [str(self.experience.pk)])
        self.assertEqual(self.client.get(self.url, {'title': 'missing'}).json(), [])
        Experience.objects.all().delete()
        self.assertEqual(self.client.get(self.url).json(), [])

    def test_page_does_not_fetch_data_on_server(self):
        from unittest.mock import patch
        with patch('main.views.get_experience_json') as get_json:
            response = self.client.get(reverse('main:show_experience'), {'title': ' develop '})
        get_json.assert_not_called()
        self.assertNotIn('experience_list', response.context)
        self.assertEqual(response.context['title_query'], 'develop')
        self.assertContains(response, 'value="develop"')
        self.assertNotContains(response, 'Developer')

    def test_skills_are_prefetched_and_include_names(self):
        other = Experience.objects.create(
            title='Other', company_name='Example', description='Other role',
            started_at=date(2025, 1, 1),
        )
        other.skills.add(self.skill)
        with self.assertNumQueries(2):
            response = self.client.get(self.url)
        self.assertEqual([item['fields']['skill_names'] for item in response.json()],
                         [['Django'], ['Django']])
        other.skills.clear()
        self.assertEqual(self.client.get(self.url).json()[1]['fields']['skill_names'], [])

    def test_page_permissions_and_endpoint_methods(self):
        editor = User.objects.create_user(username='editor')
        editor.groups.add(Group.objects.create(name='Editor'))
        owner = User.objects.create_user(username='owner', is_superuser=True)
        for user, superuser_flag, editor_flag in [(None, 'false', 'false'),
                                                  (editor, 'false', 'true'),
                                                  (owner, 'true', 'false')]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.get(reverse('main:show_experience'))
            self.assertContains(response, f'data-is-superuser="{superuser_flag}"')
            self.assertContains(response, f'data-is-editor="{editor_flag}"')
        self.assertEqual(self.client.post(self.url).status_code, 405)


class AwardAjaxTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username='owner', is_superuser=True)
        cls.editor = User.objects.create_user(username='editor')
        cls.editor.groups.add(Group.objects.create(name='Editor'))
        cls.visitor = User.objects.create_user(username='visitor')

    def setUp(self):
        self.url = reverse('main:create_award_ajax')
        self.data = {
            'title': 'New Award', 'issuer': 'University',
            'description': 'First line\nSecond line', 'awarded_at': '2026-09-30',
        }

    def test_creation_is_owner_only_and_returns_json(self):
        for user in (None, self.visitor, self.editor):
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.post(self.url, self.data)
            self.assertEqual(response.status_code, 403)
            self.assertIn('message', response.json())
        self.assertFalse(Award.objects.exists())
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        award = Award.objects.get(pk=response.json()['pk'])
        self.assertEqual(award.awarded_at, date(2026, 9, 30))
        self.assertEqual(award.description, self.data['description'])

    def test_invalid_inputs_are_not_saved(self):
        self.client.force_login(self.owner)
        for field, value in [('title', '   '), ('title', '<img src=x onerror=alert(1)>'),
                             ('title', 'a' * 256), ('issuer', '<br>'),
                             ('description', '<br>'), ('awarded_at', '2026-02-30')]:
            with self.subTest(field=field, value=value):
                response = self.client.post(self.url, {**self.data, field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()['errors'])
        self.assertFalse(Award.objects.exists())

    def test_html_is_stripped_on_ajax_and_regular_creation(self):
        self.client.force_login(self.owner)
        data = {**self.data, 'title': '<b>Winner</b>', 'issuer': '<i>University</i>',
                'description': '<p>First line</p>\nSecond line'}
        for url in (self.url, reverse('main:create_award')):
            response = self.client.post(url, data)
            self.assertIn(response.status_code, (201, 302))
        for award in Award.objects.all():
            self.assertEqual(award.title, 'Winner')
            self.assertEqual(award.issuer, 'University')
            self.assertEqual(award.description, 'First line\nSecond line')

    def test_csrf_and_post_only(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.url, self.data).status_code, 403)
        self.assertEqual(client.get(self.url).status_code, 405)
        client.get(reverse('main:show_awards'))
        response = client.post(self.url, self.data,
                               HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.assertEqual(response.status_code, 201)

    def test_page_contains_modal_only_for_owner(self):
        for user in (None, self.visitor, self.editor, self.owner):
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.get(reverse('main:show_awards'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<ol id="list" class="awards-list hide" role="list"></ol>', html=True)
            if user == self.owner:
                self.assertContains(response, 'id="award-form"')
                for field in self.data:
                    self.assertContains(response, f'name="{field}"')
            else:
                self.assertNotContains(response, 'id="award-form"')

    def test_json_search_order_and_user_star_state(self):
        award = Award.objects.create(**self.data)
        award.starred_by.add(self.visitor)
        older = Award.objects.create(**{**self.data, 'title': 'Old Award', 'awarded_at': '2025-01-01'})
        url = reverse('main:get_awards_json')
        anonymous = self.client.get(url).json()
        self.assertEqual([item['pk'] for item in anonymous], [str(award.pk), str(older.pk)])
        self.assertFalse(anonymous[0]['fields']['is_starred'])
        self.assertEqual(anonymous[0]['fields']['star_count'], 1)
        self.assertEqual(anonymous[0]['fields']['starred_by_names'], 'visitor')
        self.client.force_login(self.visitor)
        filtered = self.client.get(url, {'title': ' NEW '}).json()
        self.assertEqual(len(filtered), 1)
        self.assertTrue(filtered[0]['fields']['is_starred'])
        self.assertEqual(self.client.get(url, {'title': 'missing'}).json(), [])
