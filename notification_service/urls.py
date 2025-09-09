from django.urls import path
from . import views

app_name = 'notification_service'

urlpatterns = [
    path('', views.notifications, name="notifications"),
]