from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class ExtendedUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'user_type')