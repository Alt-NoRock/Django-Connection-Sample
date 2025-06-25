from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("create/", views.create_post, name="create_post"),
    path("delete/<int:pk>/", views.delete_post, name="delete_post"),
    path("api/posts/", views.api_posts, name="api_posts"),
    path("health/", views.health_check, name="health_check"),
]
