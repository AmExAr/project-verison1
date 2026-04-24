import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'starlift.settings')
django.setup()

from starlift.models import Speaker, Feedback

speakers = Speaker.objects.all()

for speaker in speakers:
    nps_value = speaker.calculate_nps()
    if nps_value is not None:
        speaker.nps = nps_value
    else:
        speaker.nps = 0.0
    speaker.save()

print(f"NPS успешно пересчитан и обновлен для {speakers.count()} спикеров!")
