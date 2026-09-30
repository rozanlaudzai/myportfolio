from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Award


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
