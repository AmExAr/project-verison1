from django.contrib import admin
from django.urls import path
from starlift import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name='home'),
    path('index/', views.index_view, name='index'),
    path('speakers/', views.speakers_view, name='speakers'),
    path('events/', views.events_view, name='events'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('profile/', views.profile_view, name='profile'),
    path('api/speakers/', views.speakers_api, name='speakers_api'),
    path('api/events/', views.events_api, name='events_api'),
]
