from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser


class Offer(models.Model):
    CATEGORY_CHOICES = [
        ('cleaning', '🧹 Чистене'),
        ('groceries', '🛒 Пазаруване'),
        ('transport', '🚗 Транспорт'),
        ('tech', '💻 Помощ с техника'),
        ('gardening', '🌿 Помощ с градината'),
        ('cooking', '🍲 Готвене'),
        ('other', '✨ Друго'),
    ]

    TYPE_CHOICES = [
        ('paid', 'Платена'),
        ('volunteer', 'Доброволна'),
    ]

    STATUS_CHOICES = [
        ('waiting', 'Чака отговор'),
        ('accepted', 'Прието'),
        ('completed', 'Завършено'),
    ]

    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_created',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    offer_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    city = models.CharField(max_length=100, blank=True, default='')
    address = models.CharField(max_length=200, blank=True, default='')
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        db_index=True,
    )
    accepted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_accepted',
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_completed',
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    requested_for = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_requested_for',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    contact_info = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class User(AbstractUser):
    USER_TYPES = (
        ('worker', 'Доброволец/Работник'),
        ('needer', 'Търсещ помощ'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='needer')
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.username

    @property
    def worker_phone(self):
        try:
            return self.worker_profile.phone or ''
        except WorkerProfile.DoesNotExist:
            return ''

    @property
    def average_rating(self):
        from .models import Rating
        agg = Rating.objects.filter(worker=self).aggregate(avg=Avg('overall_score'))
        return agg['avg']


class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    phone = models.CharField(max_length=30, blank=True)
    skills = models.TextField(blank=True)

    def __str__(self):
        return f"WorkerProfile({self.user.username})"


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Изчакване'),
        ('accepted', 'Прието'),
        ('rejected', 'Отхвърлено'),
    ]

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey('User', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('offer', 'worker')

    def __str__(self):
        return f"{self.worker.username} → {self.offer.title}"


class Rating(models.Model):
    offer = models.OneToOneField(
        Offer,
        on_delete=models.CASCADE,
        related_name='rating',
    )
    worker = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='ratings_received',
    )
    needer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='ratings_given',
    )
    performance = models.PositiveSmallIntegerField()
    behaviour = models.PositiveSmallIntegerField()
    speed = models.PositiveSmallIntegerField()
    overall_score = models.DecimalField(max_digits=3, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Оценка {self.overall_score}/5 за {self.worker.username} на {self.offer.title}"


class Notification(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=300)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{'ПРОЧЕТЕНО' if self.read else 'НЕПРОЧЕТЕНО'} → {self.user.username}: {self.message[:50]}"


