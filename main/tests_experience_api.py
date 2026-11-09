import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Experience, Skill


class ExperienceAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser('owner', 'owner@example.com', 'password')
        self.visitor = User.objects.create_user('visitor', password='password')
        self.editor = User.objects.create_user('editor', password='password')
        self.editor.groups.add(Group.objects.create(name='Editor'))
        self.payload = {
            'title': 'Developer', 'company_name': 'University',
            'company_logo': '', 'description': 'Built a portfolio',
            'started_at': '2026-01-01', 'ended_at': None,
        }
        self.record = Experience.objects.create(**self.payload)
        self.skill = Skill.objects.create(name='Python')
        self.record.skills.add(self.skill)
        self.list_url = reverse('api:experience-list')
        self.detail_url = reverse('api:experience-detail', args=[self.record.pk])
        self.star_url = reverse('api:experience-star', args=[self.record.pk])

    def assert_unchanged(self):
        self.record.refresh_from_db()
        self.assertEqual(Experience.objects.count(), 1)
        for field, value in self.payload.items():
            actual = getattr(self.record, field)
            self.assertEqual(str(actual) if field == 'started_at' else actual, value)
        self.assertEqual(list(self.record.skills.all()), [self.skill])
        self.assertFalse(self.record.starred_by.exists())
        self.assertEqual(Skill.objects.count(), 1)

    def test_public_reads_search_and_private_fields(self):
        self.record.starred_by.add(self.visitor)
        for user in (None, self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user)
            for url in (self.list_url, self.detail_url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                data = response.data[0] if url == self.list_url else response.data
                self.assertEqual(set(data), set(self.payload) | {'id', 'skills', 'star_count', 'is_starred'})
                self.assertEqual(data['skills'], ['Python'])
                self.assertEqual(data['star_count'], 1)
                self.assertEqual(data['is_starred'], user == self.visitor)
        self.assertEqual(len(self.client.get(self.list_url, {'title': ' DEV '}).data), 1)
        self.assertEqual(self.client.get(self.list_url, {'title': 'missing'}).data, [])

    def test_guest_and_user_writes_leave_database_unchanged(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user)
            for method, url in [('post', self.list_url), ('put', self.detail_url),
                                ('patch', self.detail_url), ('delete', self.detail_url)]:
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(url, {
                        **self.payload, 'title': 'Unauthorized', 'skills': ['Forged'],
                    }, format='json')
                    self.assertEqual(response.status_code, 403)
                    self.assert_unchanged()

    def test_editor_patch_put_and_denied_create_delete(self):
        self.client.force_authenticate(self.editor)
        self.assertEqual(self.client.patch(self.detail_url, {'title': '<b>Edited</b>'}, format='json').status_code, 200)
        self.record.refresh_from_db()
        self.assertEqual(self.record.title, 'Edited')
        self.assertEqual(self.record.description, self.payload['description'])
        self.assertEqual(list(self.record.skills.all()), [self.skill])
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)
        for method, url in [('post', self.list_url), ('delete', self.detail_url)]:
            self.assertEqual(getattr(self.client, method)(url, self.payload, format='json').status_code, 403)
            self.assert_unchanged()
        self.visitor.is_staff = True
        self.visitor.save()
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'Staff'}, format='json').status_code, 403)
        self.assert_unchanged()

    def test_owner_create_update_delete_and_readonly_fields(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, 'title': ' <b>Engineer</b> ', 'company_name': '<i>UI</i>',
            'description': '<p>Work</p>', 'skills': [' python ', 'PYTHON', '<b>Django</b>'],
            'id': str(uuid.uuid4()), 'star_count': 999, 'is_starred': True,
            'starred_by': [self.visitor.pk],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        created = Experience.objects.get(pk=response.data['id'])
        self.assertEqual((created.title, created.company_name, created.description), ('Engineer', 'UI', 'Work'))
        self.assertEqual(response.data['skills'], ['Django', 'Python'])
        self.assertEqual(response.data['star_count'], 0)
        self.assertFalse(response.data['is_starred'])
        self.assertEqual(self.client.patch(self.detail_url, {'skills': []}, format='json').status_code, 200)
        self.assertFalse(self.record.skills.exists())
        self.assertEqual(self.client.put(self.detail_url, {'title': 'Incomplete'}, format='json').status_code, 400)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertFalse(Experience.objects.filter(pk=self.record.pk).exists())
        self.assertTrue(Experience.objects.filter(pk=created.pk).exists())

    def test_validation_and_patch_date_consistency(self):
        self.client.force_authenticate(self.owner)
        for field, value in [('title', '<br>'), ('title', 'x' * 256),
                             ('company_name', '<b></b>'), ('description', ' '),
                             ('company_logo', 'javascript:alert(1)'), ('started_at', 'bad'),
                             ('ended_at', '2025-01-01'), ('skills', ['<br>']),
                             ('skills', ['x' * 256])]:
            with self.subTest(field=field, value=value):
                response = self.client.post(self.list_url, {**self.payload, field: value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
                self.assert_unchanged()
        self.assertEqual(self.client.patch(self.detail_url, {'ended_at': '2025-01-01'}, format='json').status_code, 400)
        self.assert_unchanged()
        self.client.patch(self.detail_url, {'ended_at': '2026-02-01'}, format='json')
        response = self.client.patch(self.detail_url, {'started_at': '2026-03-01'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.record.refresh_from_db()
        self.assertEqual(str(self.record.started_at), '2026-01-01')

    def test_star_uses_request_user_and_preserves_other_stars(self):
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.assert_unchanged()
        self.record.starred_by.add(self.owner)
        for user in (self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user)
            before = self.record.starred_by.filter(pk=user.pk).exists()
            response = self.client.post(self.star_url, {'user': self.visitor.pk}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['is_starred'], not before)
            self.assertEqual(self.record.starred_by.filter(pk=user.pk).exists(), not before)
            self.client.post(self.star_url)
            self.assertEqual(self.record.starred_by.filter(pk=user.pk).exists(), before)
        self.assertEqual(list(self.record.starred_by.all()), [self.owner])

    def test_missing_objects_and_methods(self):
        self.client.force_authenticate(self.owner)
        missing = reverse('api:experience-detail', args=[uuid.uuid4()])
        for method in ('get', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.client, method)(missing, {}, format='json').status_code, 404)
        self.assertEqual(self.client.post(reverse('api:experience-star', args=[uuid.uuid4()])).status_code, 404)
        self.assertEqual(self.client.get(self.star_url).status_code, 405)
        self.assertEqual(self.client.delete(self.list_url).status_code, 405)
        self.assert_unchanged()

    def test_real_session_csrf_required_for_every_write(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='owner', password='password'))
        for method, url in [('post', self.list_url), ('put', self.detail_url),
                            ('patch', self.detail_url), ('delete', self.detail_url), ('post', self.star_url)]:
            self.assertEqual(getattr(client, method)(url, self.payload, format='json').status_code, 403)
            self.assert_unchanged()
        page = client.get(self.list_url, HTTP_ACCEPT='text/html')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'rest_framework')
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.list_url, self.payload, format='json', HTTP_X_CSRFTOKEN=token).status_code, 201)
        for name in ('visitor', 'editor'):
            client.logout()
            self.assertTrue(client.login(username=name, password='password'))
            page = client.get(reverse('main:show_experience'))
            self.assertEqual(page.status_code, 200)
            token = client.cookies['csrftoken'].value
            self.assertEqual(client.post(self.star_url, HTTP_X_CSRFTOKEN=token).status_code, 200)
