from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from apps.users.models import Profile
from apps.users.forms import ProfileForm, QuillFieldForm
from apps.offers.models import Coefficient, CoefficientGroup, UserCoefficientPreference

# Create your views here.


@login_required(login_url='/accounts/login/basic-login/')
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    form = QuillFieldForm(instance=profile)
    if request.method == 'POST':

        if request.POST.get('email'):
            request.user.email = request.POST.get('email')
            request.user.save()

        for attribute, value in request.POST.items():
            if attribute == 'csrfmiddlewaretoken':
                continue

            setattr(profile, attribute, value)
            profile.save()

        messages.success(request, 'Profile updated successfully')
        return redirect(request.META.get('HTTP_REFERER'))

    context = {
        'segment': 'profile',
        'parent': 'apps',
        'form': form
    }
    return render(request, 'pages/apps/user-profile.html', context)


def upload_avatar(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        profile.avatar = request.FILES.get('avatar')
        profile.save()
        messages.success(request, 'Avatar uploaded successfully')
    return redirect(request.META.get('HTTP_REFERER'))


def change_password(request):
    user = request.user
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if new_password == confirm_new_password:
            if check_password(request.POST.get('current_password'), user.password):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully')
            else:
                messages.error(request, "Old password doesn't match!")
        else:
            messages.error(request, "Password doesn't match!")

    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url="/accounts/login/basic-login/")
def update_coefficient_preference(request):
    """Save per-group default coefficients for the current user (sidebar configurator)."""
    if request.method != "POST" or request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
    try:
        coefficient_id = request.POST.get("coefficient_id")
        group_id = request.POST.get("group_id")
        if not coefficient_id or not group_id:
            return JsonResponse(
                {"success": False, "error": "Missing coefficient_id or group_id"},
                status=400,
            )
        coefficient = get_object_or_404(Coefficient, id=coefficient_id)
        group = get_object_or_404(CoefficientGroup, id=group_id)
        if coefficient.group_id != group.id:
            return JsonResponse(
                {"success": False, "error": "Coefficient does not belong to this group"},
                status=400,
            )
        with transaction.atomic():
            UserCoefficientPreference.objects.update_or_create(
                user=request.user,
                group=group,
                defaults={"coefficient": coefficient},
            )
        return JsonResponse(
            {
                "success": True,
                "coefficient_id": coefficient.id,
                "coefficient_name": coefficient.name,
                "group_id": group.id,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required(login_url='/accounts/login/basic-login/')
def change_mode(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.dark_mode:
        profile.dark_mode = False
    else:
        profile.dark_mode = True
    
    profile.save()

    return redirect(request.META.get('HTTP_REFERER'))