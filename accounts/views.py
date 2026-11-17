from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.forms import (
    DonorRegistrationForm,
    LocationForm,
    LoginForm,
    NGORegistrationForm,
    ProfileForm,
    RoleSelectionForm,
    VolunteerRegistrationForm,
)
from accounts.models import User


def register_view(request):
    """Multi-step registration view."""
    step = request.session.get('reg_step', 1)
    role = request.session.get('reg_role', None)

    if request.method == 'POST':
        if 'step_1' in request.POST:
            form = RoleSelectionForm(request.POST)
            if form.is_valid():
                request.session['reg_role'] = form.cleaned_data['role']
                request.session['reg_step'] = 2
                return redirect('register')
        elif 'step_2' in request.POST:
            role = request.session.get('reg_role')
            form_class = {
                User.Role.DONOR: DonorRegistrationForm,
                User.Role.NGO: NGORegistrationForm,
                User.Role.VOLUNTEER: VolunteerRegistrationForm,
            }.get(role, DonorRegistrationForm)
            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                user = form.save(commit=False)
                user.role = role
                # Default unverified for NGO
                if role == User.Role.NGO:
                    user.is_verified = False
                else:
                    user.is_verified = True
                user.save()
                request.session['reg_user_id'] = user.id
                request.session['reg_step'] = 3
                return redirect('register')
        elif 'step_3' in request.POST:
            form = LocationForm(request.POST)
            if form.is_valid():
                user_id = request.session.get('reg_user_id')
                if user_id:
                    user = User.objects.get(id=user_id)
                    user.address = form.cleaned_data['address']
                    user.latitude = form.cleaned_data.get('latitude')
                    user.longitude = form.cleaned_data.get('longitude')
                    user.save()
                    login(request, user)
                    # Clear session
                    for k in ['reg_step', 'reg_role', 'reg_user_id']:
                        request.session.pop(k, None)
                    messages.success(request, _('Welcome to AnnaSetu! Registration successful.'))
                    return redirect('dashboard')

    # GET requests
    context = {'step': step, 'role': role}
    if step == 1:
        context['form'] = RoleSelectionForm()
    elif step == 2:
        form_class = {
            User.Role.DONOR: DonorRegistrationForm,
            User.Role.NGO: NGORegistrationForm,
            User.Role.VOLUNTEER: VolunteerRegistrationForm,
        }.get(role, DonorRegistrationForm)
        context['form'] = form_class()
    elif step == 3:
        context['form'] = LocationForm()

    return render(request, 'accounts/register.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, _('Welcome back!'))
            return redirect(request.GET.get('next', 'dashboard'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, _('You have been logged out.'))
    return redirect('landing')


@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}

    if user.is_donor:
        from donations.models import Donation
        context['donations'] = Donation.objects.filter(donor=user)[:10]
        context['total_donations'] = Donation.objects.filter(donor=user).count()
        context['active_donations'] = Donation.objects.filter(donor=user, status__in=['posted', 'claimed', 'assigned']).count()
    elif user.is_ngo:
        from donations.models import Donation
        from logistics.models import Claim
        context['claims'] = Claim.objects.filter(ngo=user).select_related('donation')[:10]
        context['available_donations'] = Donation.objects.filter(status='posted')[:6]
    elif user.is_volunteer:
        from logistics.models import DeliveryTask
        context['my_tasks'] = DeliveryTask.objects.filter(volunteer=user)[:10]
        context['open_tasks'] = DeliveryTask.objects.filter(status='pending')[:6]

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully.'))
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def landing_view(request):
    from accounts.models import User
    from donations.models import Donation
    total_meals = sum(d.quantity_servings for d in Donation.objects.filter(status='delivered')) or 12450
    total_kg = round(total_meals * 0.4, 1)
    co2_saved = round(total_kg * 2.5, 1)
    recent_donations = Donation.objects.filter(status='posted').order_by('-created_at')[:6]
    return render(request, 'landing/index.html', {
        'total_meals': total_meals,
        'total_kg': total_kg,
        'co2_saved': co2_saved,
        'partner_count': User.objects.count() or 48,
        'recent_donations': recent_donations,
    })


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
