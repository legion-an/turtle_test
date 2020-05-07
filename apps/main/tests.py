import datetime
from unittest import mock

import factory
import pytz
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.main.models import Commit, Author, Repository
from utils.github import APIException


class FakeResponse:

    def __init__(self, status_code, json=None, headers=None):
        self.status_code = status_code
        self.json = lambda: self.generate_commits() if json is None else json
        self.headers = headers or {}

    @staticmethod
    def generate_commits(count=5):
        today = datetime.date.today()
        return [{
            'sha': factory.Faker('sha1').generate(),
            'commit': {
                'author': {
                    'name': f'My Name {i}',
                    'email': f'email-{i}@gmail.com',
                    'date': datetime.datetime(
                        today.year, today.month, i, 6, 0, tzinfo=datetime.timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%S%z")
                },
                'message': f'Test commit {i}'
            },
            'url': f'https://github.com/commit/{i}/'
        } for i in range(1, count + 1)]


class GetCommitsFromGitHub(APITestCase):

    def tearDown(self) -> None:
        Author.objects.all().delete()

    @mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: FakeResponse(200, json=[]))
    def test_empty_request(self, *args):
        commits = Commit.get_commits_from_github('test', 'test')
        self.assertEqual(commits, [])

    def test_404_request(self):
        message = {'message': 'Not Found'}
        response_404 = FakeResponse(404, json=message)
        with mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: response_404):
            # Repo or owner doesn't exist
            with self.assertRaises(APIException) as error:
                Commit.get_commits_from_github('test', 'test')
                self.assertEqual(error.response.json(), message)

    @mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: FakeResponse(200))
    def test_good_request(self, *args):
        commits = Commit.get_commits_from_github('test', 'test')
        self.assertEqual(Author.objects.count(), 6)
        # 1 author is owner of this repo (username='test'), 5 authors are from commits
        self.assertEqual(Repository.objects.count(), 1)
        self.assertEqual(Commit.objects.count(), 5)

        today = datetime.date.today()
        for i, c in enumerate(commits, start=1):
            self.assertEqual(c.author.username, f'My Name {i}')
            self.assertEqual(c.date.date(), datetime.date(today.year, today.month, i))


class AuthorViewTestCase(APITestCase):

    def tearDown(self) -> None:
        Author.objects.all().delete()

    def test_view(self):
        url = reverse('author-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(),
            {'repository': ['This field is required.'], 'owner': ['This field is required.']}
        )

        with mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: FakeResponse(200, json=[])):
            response = self.client.get(url, data={'repository': 'test', 'owner': 'test'})
            self.assertEqual(response.status_code, 204)

        with mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: FakeResponse(200)):
            response = self.client.get(url, data={'repository': 'test', 'owner': 'test'})
            data = response.json()
            self.assertEqual(len(data['authors']), 5)
            self.assertEqual(len(data['dates']), 5)

            for author in data['authors']:
                self.assertEqual(len(author['commits']), 1)

    def test_commits_grouping(self):
        url = reverse('author-list')

        owner = Author.objects.create(username='test')
        repository = Repository.objects.create(name='test', owner=owner)
        commits = FakeResponse.generate_commits(2)
        # 1 commit for 1 user per 1 day
        commits.extend(FakeResponse.generate_commits(5))
        # 2 commits for 1-st and 2-nd date and user, rest of users and dates have only 1 commit

        fake_response = FakeResponse(200, json=commits)
        with mock.patch('utils.github.requests.get', side_effect=lambda *args, **kwargs: fake_response):
            response = self.client.get(url, data={'repository': repository.name, 'owner': owner.username})
            data = response.json()
            self.assertEqual(len(data['authors']), 5)
            self.assertEqual(len(data['dates']), 5)

            for i, author in enumerate(data['authors']):
                author_commits = author['commits']
                commits_data = author_commits[list(author_commits.keys())[0]]
                if i < 2:
                    self.assertEqual(len(commits_data), 2)
                else:
                    self.assertEqual(len(commits_data), 1)
