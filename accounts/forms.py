from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User


class RoleSelectionForm(forms.Form):
    """Step 1: Choose role."""
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.RadioSelect(attrs={'class': 'hidden peer'}),
    )


class DonorRegistrationForm(UserCreationForm):
    """Step 2: Donor details."""
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'organization_name', 'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all'})
        self.fields['email'].required = True
        self.fields['organization_name'].help_text = 'Restaurant, caterer, or leave blank for individual'


class NGORegistrationForm(UserCreationForm):
    """Step 2: NGO details."""
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'organization_name', 'verification_doc',
            'capacity_servings_per_day', 'accepts_veg_only',
            'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all'})
        self.fields['email'].required = True
        self.fields['organization_name'].required = True
        self.fields['verification_doc'].help_text = 'Upload registration certificate or ID for verification'


class VolunteerRegistrationForm(UserCreationForm):
    """Step 2: Volunteer details."""
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all'})
        self.fields['email'].required = True


class LocationForm(forms.Form):
    """Step 3: Location picker."""
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all',
            'placeholder': 'Enter your address',
        }),
    )
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())


class ProfileForm(forms.ModelForm):
    """Edit profile."""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'organization_name',
            'address', 'avatar', 'capacity_servings_per_day',
            'accepts_veg_only', 'service_radius_km', 'preferred_language',
            'email_notifications', 'sms_notifications',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'w-5 h-5 rounded border-stone-300 text-green-600 focus:ring-green-500'})
            else:
                field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all'})


class LoginForm(AuthenticationForm):
    """Styled login form."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all'})
