from django.urls import path
from .views import reset_profile_image, view_profile, edit_profile, librarian_dashboard, update_user_role, manage_users, guest_login


app_name = "user_service"  # This enables the namespace "user_service"

urlpatterns = [
    path("librarian-dashboard/", librarian_dashboard, name="librarian_dashboard"),
    path("manage-users/", manage_users, name="manage_users"),  # user managing page
    path("update-role/<int:user_id>/", update_user_role, name="update_user_role"),  # role change
    path("profile/", view_profile, name="view_profile"),
	path("profile/edit/", edit_profile, name="edit_profile"),
    path("profile/reset-image/", reset_profile_image, name="reset_profile_image"),
    path('guest-login/', guest_login, name='guest_login'),
]