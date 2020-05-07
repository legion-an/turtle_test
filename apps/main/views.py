from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, response, viewsets, status

from apps.main.models import Author, Commit
from apps.main.serializers import AuthorViewQuerySerializer, AuthorListSerializer
from utils.github import APIException


class AuthorView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorListSerializer

    @swagger_auto_schema(query_serializer=AuthorViewQuerySerializer)
    def list(self, request, *args, **kwargs):
        request_serializer = AuthorViewQuerySerializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)

        try:
            commits = Commit.get_commits_from_github(**request_serializer.validated_data)
            if not commits:
                return response.Response(status=status.HTTP_204_NO_CONTENT)
        except APIException:
            return response.Response({'detail': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)

        prefetch_commits = Commit.objects.filter(
            sha__in=[c.sha for c in commits], repository__name=request_serializer.validated_data['repository']
        )
        authors = self.get_queryset().filter(id__in=[c.author_id for c in commits]).prefetch_related(
            Prefetch('commit_set', queryset=prefetch_commits)
        )
        serializer = self.get_serializer(authors, many=True)

        return response.Response({
            'authors': serializer.data,
            'dates': sorted({c.date.date() for c in commits})
        })
