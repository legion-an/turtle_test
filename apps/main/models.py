import datetime
import json
from typing import List

from django.db import models

from utils.github import Client


class Author(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True)


class Repository(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'owner')


class Commit(models.Model):
    sha = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    date = models.DateTimeField()
    data = models.TextField(help_text='Commit data in json format')

    class Meta:
        unique_together = ('repository', 'sha')

    @staticmethod
    def get_commits_from_github(owner, repository, author=None, since=None, until=None) -> List['Commit']:
        """
        get commits from github via API
        create Authors that are not in our database
        create Commits and link them with Repository and Authors

        :param owner: username
        :param repository: name
        :param author: username
        :param since: datetime
        :param until: datetime
        :return: Commit objects
        """

        commits = Client().get_commits(owner, repository, author=author, since=since, until=until)

        owner_obj, _ = Author.objects.get_or_create(username=owner)
        repository_obj, _ = Repository.objects.get_or_create(name=repository, owner=owner_obj)

        if not commits:
            return []

        return Commit.create_commits(repository_obj, commits)

    @staticmethod
    def create_commits(repository: Repository, commits: List[dict]) -> List['Commit']:
        """
        create Authors that are not in our database
        create Commits and link them with Repository and Authors

        :return: Commit objects
        """

        authors = {commit['commit']['author']['name']: commit['commit']['author'] for commit in commits}
        existing_authors = {a.username: a for a in Author.objects.filter(username__in=authors)}
        bulk = []
        for name, author in authors.items():
            existing_author = existing_authors.get(name)
            if not existing_author:
                bulk.append(
                    Author(username=name, email=author['email'])
                )
            elif not existing_author.email:
                # update owner's email
                existing_author.email = author['email']
                existing_author.save()

        created_authors = {a.username: a for a in Author.objects.bulk_create(bulk)}
        existing_authors.update(created_authors)

        commits_bulk = []
        for commit in commits:
            commits_bulk.append(
                Commit(
                    sha=commit['sha'],
                    author=existing_authors[commit['commit']['author']['name']],
                    repository=repository,
                    date=datetime.datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%S%z"),
                    data=json.dumps({'message': commit['commit']['message'], 'url': commit['url']})
                )
            )
        return Commit.objects.bulk_create(commits_bulk, ignore_conflicts=True)
