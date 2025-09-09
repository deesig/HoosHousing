from django.urls import path
from . import views

app_name = 'leasing_service'

urlpatterns = [
    path('submit-lease-request/<int:property_id>/', views.submit_lease_request, name="submit_lease_request"),
    path('manage-lease-requests/', views.manage_lease_requests, name="manage_lease_requests"),
    path('my-leases/', views.my_leases, name="my_leases"),
    path('cancel-lease/<int:lease_id>/', views.cancel_lease, name='cancel_lease'),
]
