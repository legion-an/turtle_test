from rest_framework import routers

from apps.main.views import AuthorView


router = routers.SimpleRouter()
router.register('authors', AuthorView)
