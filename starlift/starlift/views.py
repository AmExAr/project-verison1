from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import user_passes_test
from .models import Speaker, Event
from .forms import SpeakerForm

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
    try:
        speakers = Speaker.objects.all()
        speakers_data = []
        for speaker in speakers:
            speakers_data.append({
                "id": speaker.id,
                "name": speaker.name,
                "sub": speaker.sub,
                "stack": speaker.stack,
                "city": speaker.city,
                "status": speaker.status,
                "nps": float(speaker.nps) if speaker.nps else 0.0,
                "img": speaker.img,
                "events": []
            })
        return JsonResponse(speakers_data, safe=False)
    except Exception as e:
        print(f"Error fetching speakers: {e}")
        return JsonResponse([], safe=False)

def events_api(request):
    try:
        events = Event.objects.all()
        events_data = []
        for event in events:
            # Check if there is some useful info
            is_empty_desc = not event.description or event.description.lower() == 'none' or event.description.strip() == ''
            is_empty_link = not event.link or event.link.lower() == 'none' or event.link.strip() == ''
            
            if is_empty_desc and is_empty_link:
                continue
                
            events_data.append({
                "id": event.id,
                "title": event.title,
                "status": event.status,
                "date": event.date,
                "location": event.location,
                "link": event.link,
                "description": event.description,
                "schedule": event.schedule
            })
            
        # Sort so that 'past' events are at the bottom
        events_data.sort(key=lambda x: (1 if x['status'] == 'past' else 0, x['date'] if x['date'] else ''))
        
        return JsonResponse(events_data, safe=False)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return JsonResponse([], safe=False)

@user_passes_test(lambda u: u.is_superuser)
def speaker_add(request):
    if request.method == 'POST':
        form = SpeakerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('speakers')
    else:
        form = SpeakerForm()
    return render(request, 'speaker_form.html', {'form': form, 'title': 'Добавить спикера'})

@user_passes_test(lambda u: u.is_superuser)
def speaker_edit(request, pk):
    speaker = get_object_or_404(Speaker, pk=pk)
    if request.method == 'POST':
        form = SpeakerForm(request.POST, request.FILES, instance=speaker)
        if form.is_valid():
            form.save()
            return redirect('speakers')
    else:
        form = SpeakerForm(instance=speaker)
    return render(request, 'speaker_form.html', {'form': form, 'title': 'Редактировать спикера'})

@user_passes_test(lambda u: u.is_superuser)
def speaker_delete(request, pk):
    speaker = get_object_or_404(Speaker, pk=pk)
    if request.method == 'POST':
        speaker.delete()
        return redirect('speakers')
    return render(request, 'speaker_confirm_delete.html', {'speaker': speaker})
