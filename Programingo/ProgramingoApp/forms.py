from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import UserProfile

input_style = {'class': 'auth-input', 'autocomplete': 'off'}

class CustomLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Password'})
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if '@' not in email or not email.endswith('.com'):
            raise ValidationError("Enter a valid email address.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        return password


class CustomRegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': 'Repeat Password'})
    )

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(r'^[A-Za-z0-9]+$', name):
            raise ValidationError("Name must not contain special characters.")
        return name

    def clean_email(self):
        email = self.cleaned_data['email']
        if '@' not in email or not email.endswith('.com'):
            raise ValidationError("Email must contain '@' and end with '.com'.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(label="New Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Current Password")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email']
        if User.objects.filter(email=new_email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return new_email

class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']