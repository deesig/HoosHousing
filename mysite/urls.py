"""
URL configuration for pages project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from .views import landing, home, login_cancelled, login_cancelled_3rdparty

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/3rdparty/login/cancelled/", login_cancelled_3rdparty, name="thirdparty_login_cancelled"),
    path('accounts/social/login/cancelled/', login_cancelled, name="socialaccount_login_cancelled"),
    path('accounts/', include('allauth.urls')),
	path("user/", include("user_service.urls")),
    path('listings/', include('listing_service.urls')),
    path("reviews/", include("review_service.urls", namespace="review_service")),
    path('leasing/', include('leasing_service.urls')),
    path('notifications/', include('notification_service.urls')),
    path('', landing, name='home'),
]
