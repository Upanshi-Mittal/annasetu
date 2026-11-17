from django import forms
from django.utils import timezone

from donations.models import Donation


class DonationForm(forms.ModelForm):
    """Create or edit a donation listing."""

    class Meta:
        model = Donation
        fields = [
            'title', 'description', 'food_type', 'is_cooked',
            'quantity_servings', 'photo', 'pickup_address',
            'latitude', 'longitude', 'pickup_from', 'safe_until',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. 50 plates of dal-chawal',
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe the food, packaging, special notes...',
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
            'food_type': forms.RadioSelect(attrs={'class': 'hidden peer'}),
            'quantity_servings': forms.NumberInput(attrs={
                'min': 1, 'max': 10000,
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
            'pickup_address': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Full pickup address',
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'pickup_from': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
            'safe_until': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        pickup_from = cleaned.get('pickup_from')
        safe_until = cleaned.get('safe_until')

        if pickup_from and safe_until:
            if safe_until <= pickup_from:
                raise forms.ValidationError('"Safe until" must be after the pickup time.')
            if safe_until <= timezone.now():
                raise forms.ValidationError('"Safe until" must be in the future.')

        return cleaned


class ClaimForm(forms.Form):
    """NGO claim form."""
    servings_requested = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Any notes for the donor...',
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )


class FoodSafetyChecklistForm(forms.Form):
    """Food safety checklist completed before pickup."""
    temperature_ok = forms.BooleanField(
        required=True,
        label='Temperature is acceptable',
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-stone-300 text-green-600 focus:ring-green-500'}),
    )
    packaging_ok = forms.BooleanField(
        required=True,
        label='Packaging is intact and clean',
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-stone-300 text-green-600 focus:ring-green-500'}),
    )
    smell_ok = forms.BooleanField(
        required=True,
        label='No unusual smell',
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-stone-300 text-green-600 focus:ring-green-500'}),
    )
    within_safe_time = forms.BooleanField(
        required=True,
        label='Within safe consumption time',
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-stone-300 text-green-600 focus:ring-green-500'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Additional notes...',
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )


class RatingForm(forms.Form):
    """Post-delivery rating form."""
    score = forms.IntegerField(
        min_value=1, max_value=5,
        widget=forms.HiddenInput(),
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Share your experience...',
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )


class ReportForm(forms.Form):
    """Report abuse/fraud."""
    from moderation.models import Report
    reason = forms.ChoiceField(
        choices=Report.Reason.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Describe the issue...',
            'class': 'w-full px-4 py-3 rounded-xl border border-stone-300 dark:border-stone-600 bg-white dark:bg-stone-800 text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
    )
