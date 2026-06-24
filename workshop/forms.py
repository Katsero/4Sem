from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re
from .models import User, Appointment, Order


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'appointment_datetime', 'note']
        widgets = {
            'appointment_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class CheckoutForm(forms.Form):
    address = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={'placeholder': 'ул. Примерная, д. 1, Москва, 101000'}),
    )
    phone = forms.CharField(max_length=20)
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        regex = r'^[а-яА-ЯёЁa-zA-Z\s\-\.,]+,\s*д\.\s*\d+[а-яА-Яa-zA-Z]?(?:,\s*кв\.\s*\d+)?,\s*[а-яА-ЯёЁa-zA-Z\s\-]+,\s*\d{6}$'
        if not re.match(regex, address):
            raise ValidationError(
                'Адрес должен быть в формате: "ул. Примерная, д. 1, Москва, 101000" '
                '(улица, дом, город, индекс).'
            )
        return address