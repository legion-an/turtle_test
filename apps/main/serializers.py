import json

from rest_framework import serializers

from apps.main.models import Author, Commit


class CommitSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Commit
        fields = ('sha', 'data')

    @staticmethod
    def get_data(obj):
        if obj.data:
            return json.loads(obj.data)
        return {}


class AuthorListSerializer(serializers.ModelSerializer):
    commits = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = '__all__'

    @staticmethod
    def get_commits(obj) -> dict:
        dates = {}
        for commit in obj.commit_set.all():
            dates.setdefault(commit.date.date().isoformat(), []).append(CommitSerializer(commit).data)
        return dates


class AuthorViewQuerySerializer(serializers.Serializer):
    repository = serializers.CharField()
    owner = serializers.CharField()
    author = serializers.CharField(required=False)
    since = serializers.DateField(required=False)
    until = serializers.DateField(required=False)
