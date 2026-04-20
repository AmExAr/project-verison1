from django.shortcuts import render
from django.http import JsonResponse
from .models import Speaker


def index_view(request):
    return render(request, 'index.html')

def speakers_view(request):
    return render(request, 'speakers.html')

def events_view(request):
    return render(request, 'events.html')

def analytics_view(request):
    return render(request, 'analytics.html')

def profile_view(request):
    return render(request, 'profile.html')

def speakers_api(request):
    speakers = Speaker.objects.prefetch_related('events').all()
    speakers_data = []
    for speaker in speakers:
        events = [{"t": event.title, "s": event.status} for event in speaker.events.all()]
        speakers_data.append({
            "id": speaker.id,
            "name": speaker.name,
            "sub": speaker.sub,
            "stack": speaker.stack,
            "city": speaker.city,
            "status": speaker.status,
            "nps": float(speaker.nps),
            "img": speaker.img,
            "events": events
        })
    return JsonResponse(speakers_data, safe=False)
