from allauth.account.models import Login
from django.utils.text import get_valid_filename
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import redirect_to_login

@login_required
def reset_profile_image(request):
    # Clear out the profile_image field
    request.user.profile_image = None
    request.user.save()
    messages.success(request, "Profile picture reset to default.")
    return redirect('user_service:edit_profile')

from user_service.models import CustomUser  # ✅ Import CustomUser model

# Decorator to check if the user is a Librarian
def is_librarian(user):
    return user.role == "librarian"

def not_guest(user):
    return user.is_authenticated and user.role != 'guest'

@login_required
@user_passes_test(is_librarian)  # Only accessible by Librarians
def librarian_dashboard(request):
    return render(request, "user_service/librarian_dashboard.html")

@login_required
@user_passes_test(is_librarian)  # Only accessible by Librarians
def manage_users(request):
    search_query = request.GET.get('search', '')
    
    # Base queryset
    users = CustomUser.objects.all()
    
    # Apply search filter if a search query exists
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) | 
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    # Order the results
    users = users.order_by("username")
    
    return render(request, "user_service/manage_users.html", {
        "users": users,
    })


@login_required
@user_passes_test(is_librarian)  # Only accessible by Librarians
def update_user_role(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        new_role = request.POST.get("role")

        # Prevent a librarian from modifying another librarian's role
        if user.role == "librarian":
            messages.error(request, "You cannot change another librarian's role.")
            return redirect("user_service:manage_users")

        # Only patrons can be promoted to librarians
        if new_role == "librarian" and user.role != "patron":
            messages.error(request, "Only patrons can be promoted to librarians.")
            return redirect("user_service:manage_users")

        if new_role in ["librarian", "patron"]:
            user.role = new_role
            user.save()
            messages.success(request, f"{user.username}'s role has been updated to {new_role}.")

    return redirect("user_service:manage_users")

@login_required
@user_passes_test(not_guest)
def view_profile(request):
    user = request.user
    return render(request, "user_service/profile.html", {"user": user})

@login_required
@user_passes_test(not_guest)
def edit_profile(request):
    user = request.user  # Get the currently logged-in user

    if request.method == 'POST':
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        profile_image = request.FILES.get("profile_image")

        # Validate password confirmation
        if password and password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("user_service:edit_profile")

        # Update username if provided
        if username:
            if CustomUser.objects.exclude(id=user.id).filter(username=username).exists():
                messages.error(request, "This username is already taken.")
                return redirect("user_service:edit_profile")
            user.username = username
        
        # Update first name if provided
        if first_name:
            user.first_name = first_name
        
        # Update last name if provided
        if last_name:
            user.last_name = last_name

        # Update password (must use set_password)
        if password:
            user.set_password(password)
            update_session_auth_hash(request, user)  # Prevent logout after password change

        # Upload profile image to S3 and save the full URL in the user model
        if profile_image:
            try:
                s3_storage = S3Boto3Storage()  # ✅ Force S3 storage usage
                file_name = f"profile-image/{user.id}_{profile_image.name}"
                saved_file_path = s3_storage.save(file_name, ContentFile(profile_image.read()))

                # Store full S3 URL in the user profile_image field
                user.profile_image = f"{settings.AWS_S3_CUSTOM_DOMAIN}/{saved_file_path}"
            except Exception as e:
                messages.error(request, f"Failed to upload image: {str(e)}")
                return redirect("user_service:edit_profile")

        # Save changes
        user.save()
        messages.success(request, "Profile updated successfully!")

        return redirect("user_service:edit_profile")

    return render(request, "user_service/edit_profile.html", {"user": user})

# Guest Login
User = get_user_model()

def guest_login(request):
    try:
        guest_user = User.objects.get(username='guest')
        login(request, guest_user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('/listings/')
    except User.DoesNotExist:
        messages.error(request, "Guest account does not exist.")
        return redirect('account_login')

def guest_or_login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return view_func(request, *args, **kwargs)
    return _wrapped_view