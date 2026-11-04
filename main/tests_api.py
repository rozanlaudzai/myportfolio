import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Award


class AwardAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser('owner', 'owner@example.com', 'test-password')
        cls.visitor = User.objects.create_user('visitor', password='test-password')
        cls.editor = User.objects.create_user('editor', password='test-password')
        cls.editor.groups.add(Group.objects.create(name='Editor'))

    def setUp(self):
        self.payload = {
            'title': 'Portfolio Award', 'issuer': 'University',
            'description': 'My achievement', 'awarded_at': '2026-10-01',
        }
        self.award = Award.objects.create(**self.payload)
        self.list_url = reverse('api:award-list')
        self.detail_url = reverse('api:award-detail', args=[self.award.pk])
        self.star_url = reverse('api:award-star', args=[self.award.pk])

    def test_public_list_and_detail(self):
        for url in (self.list_url, self.detail_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = response.data[0] if url == self.list_url else response.data
            self.assertEqual(data['id'], str(self.award.pk))
            self.assertFalse(data['is_starred'])
            self.assertNotIn('fields', data)
            self.assertEqual(set(data), set(self.payload) | {
                'id', 'star_count', 'is_starred', 'starred_by_names',
            })

    def test_search_order_and_empty_results(self):
        older = Award.objects.create(**{**self.payload, 'awarded_at': '2025-01-01'})
        first = Award.objects.create(**{**self.payload, 'title': 'A prize'})
        response = self.client.get(self.list_url)
        self.assertEqual([item['id'] for item in response.data],
                         [str(first.pk), str(self.award.pk), str(older.pk)])
        self.assertEqual(len(self.client.get(self.list_url, {'title': ' PORT '}).data), 2)
        self.assertEqual(self.client.get(self.list_url, {'title': 'missing'}).data, [])
        Award.objects.all().delete()
        self.assertEqual(self.client.get(self.list_url).data, [])

    def test_missing_award(self):
        for name in ('award-detail', 'award-star'):
            url = reverse(f'api:{name}', args=[uuid.uuid4()])
            self.client.force_authenticate(self.owner)
            response = self.client.post(url) if name == 'award-star' else self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format='json').status_code, 403)
            for method in ('put', 'patch'):
                self.assertEqual(getattr(self.client, method)(self.detail_url, self.payload, format='json').status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, self.payload['title'])
        self.assertEqual(Award.objects.count(), 1)

    def test_owner_can_create_and_strip_html(self):
        self.client.force_authenticate(self.owner)
        data = {**self.payload, 'title': '<b>Winner</b>', 'issuer': '<i>UI</i>',
                'description': '<p>First</p>\nSecond'}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        created = Award.objects.get(pk=response.data['id'])
        self.assertEqual((created.title, created.issuer, created.description),
                         ('Winner', 'UI', 'First\nSecond'))

    def test_validation(self):
        self.client.force_authenticate(self.owner)
        for field, value in [('title', '   '), ('title', '<img src=x onerror=alert(1)>'),
                             ('title', 'x' * 256), ('issuer', '<br>'),
                             ('description', '<br>'), ('awarded_at', '2026-02-30')]:
            with self.subTest(field=field, value=value):
                response = self.client.post(self.list_url, {**self.payload, field: value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        self.assertEqual(Award.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail_url, {'title': 'Changed'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Changed')
        self.assertEqual(self.award.description, self.payload['description'])
        self.assertEqual(self.client.put(self.detail_url, {'title': 'Incomplete'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertFalse(Award.objects.exists())

    def test_star_requires_login_and_toggles_for_current_user(self):
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.award.starred_by.add(self.owner)
        self.client.force_authenticate(self.visitor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_starred'])
        self.assertEqual(response.data['star_count'], 2)
        self.assertEqual(set(response.data['starred_by_names'].split(', ')), {'owner', 'visitor'})
        self.assertTrue(self.client.get(self.list_url).data[0]['is_starred'])
        response = self.client.post(self.star_url)
        self.assertFalse(response.data['is_starred'])
        self.assertEqual(response.data['star_count'], 1)
        self.assertTrue(self.award.starred_by.filter(pk=self.owner.pk).exists())

    def test_computed_fields_and_id_are_read_only(self):
        self.client.force_authenticate(self.owner)
        forged_id = uuid.uuid4()
        response = self.client.post(self.list_url, {
            **self.payload, 'id': str(forged_id), 'star_count': 99, 'is_starred': True,
            'starred_by_names': 'forged', 'starred_by': [self.visitor.pk],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data['id'], str(forged_id))
        self.assertEqual(response.data['star_count'], 0)
        self.assertFalse(response.data['is_starred'])
        self.assertEqual(response.data['starred_by_names'], '')

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.client.force_authenticate(self.editor)
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'Edited'}, format='json').status_code, 200)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)
        self.assertEqual(self.client.post(self.list_url, self.payload, format='json').status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.visitor.is_staff = True
        self.visitor.save()
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'Staff'}, format='json').status_code, 403)

    def test_wrong_methods_and_safe_requests(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, 405)
        self.assertEqual(self.client.get(self.star_url).status_code, 405)
        for url in (self.list_url, self.detail_url):
            self.assertEqual(self.client.head(url).status_code, 200)
            self.assertEqual(self.client.options(url).status_code, 200)
        self.assertEqual(Award.objects.count(), 1)
        self.assertFalse(self.award.starred_by.exists())

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='owner', password='test-password'))
        for method, url, data in [('post', self.list_url, self.payload),
                                  ('patch', self.detail_url, {'title': 'Changed'}),
                                  ('delete', self.detail_url, {}), ('post', self.star_url, {})]:
            self.assertEqual(getattr(client, method)(url, data, format='json').status_code, 403)
        self.assertEqual(Award.objects.count(), 1)
        self.assertFalse(self.award.starred_by.exists())

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username='owner', password='test-password')
        page = client.get(self.list_url, HTTP_ACCEPT='text/html')
        self.assertEqual(page.status_code, 200)
        token = client.cookies['csrftoken'].value
        response = client.post(self.list_url, self.payload, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        client.logout()
        client.login(username='visitor', password='test-password')
        self.assertEqual(client.get(reverse('main:show_awards')).status_code, 200)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.star_url, HTTP_X_CSRFTOKEN=token).status_code, 200)
