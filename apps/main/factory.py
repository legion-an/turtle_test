import factory

from apps.main.models import Author, Repository, Commit


class AuthorFactory(factory.DjangoModelFactory):
    email = factory.Faker('email')
    username = factory.Faker('user_name')

    class Meta:
        model = Author


class RepositoryFactory(factory.DjangoModelFactory):
    name = factory.Faker('user_name')
    owner = factory.SubFactory(AuthorFactory)

    class Meta:
        model = Repository


class CommitFactory(factory.DjangoModelFactory):
    sha = factory.Faker('sha1')
    author = factory.SubFactory(AuthorFactory)
    repository = factory.SubFactory(RepositoryFactory)
    date = factory.Faker('date')
    data = factory.Dict({
        'message': factory.Faker('sentence'),
        'url': factory.Faker('url')
    })

    class Meta:
        model = Commit
