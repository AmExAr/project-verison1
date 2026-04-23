from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
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
    path('speakers/add/', views.speaker_add, name='speaker_add'),
    path('speakers/edit/<int:pk>/', views.speaker_edit, name='speaker_edit'),
    path('speakers/delete/<int:pk>/', views.speaker_delete, name='speaker_delete'),
    path('speaker/<int:speaker_id>/event/<int:event_id>/qr/', views.generate_qr_view, name='generate_qr'),
    path('qr-generator/', views.qr_generator_view, name='qr_generator'),
    path('rate/<int:event_id>/<int:speaker_id>/', views.submit_feedback_view, name='rate_speaker'),
    path('thanks/', views.thank_you_view, name='thank_you'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
