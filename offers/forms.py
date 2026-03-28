from django import forms
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal, InvalidOperation

from .models import User, WorkerProfile


class BaseSignupForm(UserCreationForm):
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_latitude'}))
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_longitude'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'address', 'latitude', 'longitude')
        widgets = {
            'address': forms.TextInput(attrs={
                'id': 'id_address_input',
                'autocomplete': 'off',
                'placeholder': 'Въведете адрес',
            }),
        }

    def _to_decimal_6(self, value):
        if value is None or value == "":
            return None
        precision = Decimal('0.000001')
        return Decimal(str(value)).quantize(precision)

    def clean(self):
        cleaned_data = super().clean()
        address = (cleaned_data.get('address') or '').strip()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')

        if address and (lat is None or lng is None):
            self.add_error('address', 'Моля, изберете адрес от предложенията.')
            return cleaned_data

        try:
            cleaned_data['latitude'] = self._to_decimal_6(lat)
            cleaned_data['longitude'] = self._to_decimal_6(lng)
        except (InvalidOperation, TypeError, ValueError):
            pass

        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        if lat is not None and lng is not None:
            if not (41.2 <= float(lat) <= 44.3 and 22.3 <= float(lng) <= 28.7):
                self.add_error('address', 'Моля, изберете адрес в България.')

        return cleaned_data


class NeederSignupForm(BaseSignupForm):
    email = forms.EmailField(required=True, label='Имейл')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'needer'
        if commit:
            user.save()
        return user


class WorkerSignupForm(BaseSignupForm):
    phone = forms.CharField(
        max_length=30,
        required=True,
        label='Телефон',
        widget=forms.TextInput(attrs={'placeholder': '+359...'})
    )
    skills = forms.CharField(
        required=True,
        label='Умения',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишете вашите умения...'})
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'worker'
        if commit:
            user.save()
            WorkerProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
                skills=self.cleaned_data.get('skills', ''),
            )
        return user