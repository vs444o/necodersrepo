from django import forms
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal, InvalidOperation
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from .models import User

class ExtendedUserCreationForm(UserCreationForm):
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_latitude'}))
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_longitude'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'user_type', 'address', 'latitude', 'longitude')
        widgets = {
            'address': forms.TextInput(attrs={'id': 'id_address_input', 'autocomplete': 'off'}),
        }

    def _geocode_with_nominatim(self, address):
        params = urlencode({
            'format': 'jsonv2',
            'q': address,
            'limit': 1,
            'countrycodes': 'bg',
        })
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        request = Request(url, headers={'User-Agent': 'HelpNow/1.0 (signup geocoder)'})
        with urlopen(request, timeout=4) as response:
            payload = json.loads(response.read().decode('utf-8'))

        if not payload:
            return None
        first = payload[0]
        lat = first.get('lat')
        lon = first.get('lon')
        if lat is None or lon is None:
            return None
        return lat, lon

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

        # If the frontend didn't provide lat/lng but provided address, try geocoding
        if address and (lat is None or lng is None):
            resolved = None
            try:
                resolved = self._geocode_with_nominatim(address)
            except Exception:
                resolved = None

            if resolved is not None:
                try:
                    lat = self._to_decimal_6(resolved[0])
                    lng = self._to_decimal_6(resolved[1])
                    cleaned_data['latitude'] = lat
                    cleaned_data['longitude'] = lng
                except (InvalidOperation, TypeError, ValueError):
                    pass
        else:
            # Quantize whatever came from frontend (Google/Nominatim) to 6 decimals
            try:
                cleaned_data['latitude'] = self._to_decimal_6(lat)
                cleaned_data['longitude'] = self._to_decimal_6(lng)
            except (InvalidOperation, TypeError, ValueError):
                pass

        # Final check for Bulgaria boundaries
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        if lat is not None and lng is not None:
            if not (41.2 <= float(lat) <= 44.3 and 22.3 <= float(lng) <= 28.7):
                self.add_error('address', 'Selected address must be in Bulgaria.')

        return cleaned_data

    def full_clean(self):
        """
        Custom bypass for strict password validation rules.
        This intercepts the errors after they are generated and clears 
        the ones blocking you from using simple passwords.
        """
        super().full_clean()
        if 'password1' in self._errors:
            # We keep only the error if passwords don't match.
            # We remove "too common", "entirely numeric", "no uppercase", etc.
            new_pw_errors = [
                error for error in self._errors['password1'] 
                if "match" in str(error).lower() or "too short" in str(error).lower()
            ]
            
            if not new_pw_errors:
                del self._errors['password1']
            else:
                self._errors['password1'] = new_pw_errors