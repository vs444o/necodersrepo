from django.db import models

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

    name = models.CharField(max_length=100)        # who's posting
    title = models.CharField(max_length=200)        # headline
    description = models.TextField()               # details
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    offer_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title