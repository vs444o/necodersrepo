from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class ExtendedUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'user_type', 'address', 'latitude', 'longitude')
        widgets = {
            'address': forms.TextInput(attrs={'id': 'id_address_input', 'autocomplete': 'off'}),
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        address = (cleaned_data.get('address') or '').strip()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')

        if address and (lat is None or lng is None):
            self.add_error('address', 'Please choose an address from the Bulgaria suggestions.')
            return cleaned_data

        if lat is not None and lng is not None:
            # Bulgaria bounding box (approx): lat 41.2..44.3, lon 22.3..28.7
            if not (41.2 <= float(lat) <= 44.3 and 22.3 <= float(lng) <= 28.7):
                self.add_error('address', 'Selected address must be in Bulgaria.')

        return cleaned_data