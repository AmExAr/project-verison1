import qrcode
import base64
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import user_passes_test
from .models import Speaker, Event, Feedback
from .forms import SpeakerForm, FeedbackForm

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def submit_feedback_view(request, event_id, speaker_id):
    event = get_object_or_404(Event, pk=event_id)
    speaker = get_object_or_404(Speaker, pk=speaker_id)
    
    # Session handling
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    ip_address = get_client_ip(request)
    
    # Check if already voted
    has_voted = request.COOKIES.get(f'voted_{event.id}_{speaker.id}') == 'true' or Feedback.objects.filter(
        event=event, 
        speaker=speaker, 
        session_key=session_key
    ).exists() or Feedback.objects.filter(
        event=event, 
        speaker=speaker, 
        ip_address=ip_address
    ).exists()
    
    if has_voted:
        success_msg = request.COOKIES.get(f'voted_{event.id}_{speaker.id}') == 'true'
        return render(request, 'rate_speaker.html', {
            'event': event,
            'speaker': speaker,
            'already_voted': True,
            'success_msg': success_msg
        })

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.event = event
            feedback.speaker = speaker
            feedback.session_key = session_key
            feedback.ip_address = ip_address

            # Rate limiting
            from django.utils import timezone
            from datetime import timedelta
            recent_feedback = Feedback.objects.filter(ip_address=ip_address, created_at__gte=timezone.now() - timedelta(minutes=1)).exists()
            if recent_feedback:
                return render(request, 'rate_speaker.html', {
                    'event': event, 
                    'speaker': speaker, 
                    'error': 'Слишком много запросов. Подождите минуту.'
                })

            feedback.save()
            response = render(request, 'rate_speaker.html', {
                'event': event,
                'speaker': speaker,
                'already_voted': True,
                'success_msg': True
            })
            response.set_cookie(f'voted_{event.id}_{speaker.id}', 'true', max_age=315360000)
            return response
    else:
        form = FeedbackForm()
        
    return render(request, 'rate_speaker.html', {
        'form': form,
        'event': event,
        'speaker': speaker,
        'already_voted': False
    })

def thank_you_view(request):
    return render(request, 'thank_you.html')

def index_view(request):
    return render(request, 'index.html')

def speakers_view(request):
    return render(request, 'speakers.html')

def events_view(request):
    return render(request, 'events.html')

def analytics_view(request):
    speaker_id = request.GET.get('speaker_id')
    if speaker_id:
        speaker = get_object_or_404(Speaker, id=speaker_id)
    else:
        speaker = Speaker.objects.first()

    nps_score = None
    total_feedbacks = 0
    feedbacks = []

    if speaker:
        nps_score = speaker.calculate_nps()
        qs = speaker.feedbacks.all().order_by('-created_at')
        total_feedbacks = qs.count()
        feedbacks = qs

    speakers = Speaker.objects.all()

    context = {
        'speaker': speaker,
        'speakers': speakers,
        'nps_score': nps_score,
        'total_feedbacks': total_feedbacks,
        'feedbacks': feedbacks,
    }
    return render(request, 'analytics.html', context)

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

def qr_generator_view(request):
    speakers = Speaker.objects.all()
    events = Event.objects.all()
    return render(request, 'qr_generator.html', {'speakers': speakers, 'events': events})

def generate_qr_view(request, speaker_id, event_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)
    event = get_object_or_404(Event, id=event_id)

    # Формируем URL для страницы оценки
    rate_url = f"/rate/{event_id}/{speaker_id}/"
    full_url = request.build_absolute_uri(rate_url)

    # Генерируем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    context = {
        'qr_image_base64': img_str,
        'speaker': speaker,
        'event': event,
    }
    return render(request, 'qr_display.html', context)
