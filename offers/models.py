from django.db import models
from django.contrib.auth.models import AbstractUser

class Offer(models.Model):
    CATEGORY_CHOICES = [
        ('cleaning', '🧹 Cleaning'),
        ('groceries', '🛒 Groceries'),
        ('transport', '🚗 Transport'),
        ('tech', '💻 Tech Help'),
        ('gardening', '🌿 Gardening'),
        ('cooking', '🍲 Cooking'),
        ('other', '✨ Other'),
    ]

    TYPE_CHOICES = [
        ('paid', 'Paid'),
        ('volunteer', 'Volunteer'),
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
    address = models.CharField(max_length=200, blank=True, default='')
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('accepted', 'Accepted'),
        ('completed', 'Done'),
    ]
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
        ('worker', 'Volunteer / Worker'),
        ('needer', 'Help Needer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='needer')
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.username
