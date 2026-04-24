import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Speaker(models.Model):
    name = models.CharField(max_length=200)
    sub = models.CharField(max_length=200)
    stack = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    nps = models.IntegerField(default=0)
    img = models.CharField(max_length=100)

    class Meta:
        db_table = 'starlift_speaker'

    @property
    def avatar_url(self):
        if self.img:
            if self.img.startswith('/media/') or self.img.startswith('http'):
                return self.img
            return f"https://i.pravatar.cc/150?img={self.img}"
        return ""

    def calculate_nps(self, event_id=None):
        qs = self.feedbacks.all()
        if event_id:
            qs = qs.filter(event_id=event_id)
        
        from django.db.models import Count, Q
        stats = qs.aggregate(
            total=Count('id'),
            promoters=Count('id', filter=Q(score__gte=9)),
            detractors=Count('id', filter=Q(score__lte=6))
        )
        total = stats['total']

        if total == 0:
            return 0  # Возвращаем 0, если нет отзывов
            
        nps_score = ((stats['promoters'] - stats['detractors']) / total) * 100
        return int(round(nps_score))

    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=50) # 'past' or 'future'
    date = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    link = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    schedule = models.TextField(null=True, blank=True)
    speakers = models.ManyToManyField(Speaker, related_name='events')

    class Meta:
        db_table = 'starlift_event'

    def __str__(self):
        return f"{self.title} ({self.status})"

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Спикер")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Мероприятие")
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="Оценка")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="Ключ сессии")

    class Meta:
        db_table = 'starlift_feedback'
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        constraints = [
            models.CheckConstraint(condition=models.Q(score__gte=0) & models.Q(score__lte=10), name='valid_score_range')
        ]

    def __str__(self):
        return f"Feedback for {self.speaker.name} at {self.event.title} - Score: {self.score}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Пересчитываем NPS для спикера при каждом новом отзыве
        nps_value = self.speaker.calculate_nps()
        if nps_value is not None:
            self.speaker.nps = nps_value
            self.speaker.save(update_fields=['nps'])
