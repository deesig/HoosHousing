from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

@login_required
def home(request):
    user = request.user

    if getattr(user, "role", None) == "librarian":
        return render(request, "home_librarian.html", {"user": user})  # 사서 화면
    else:
        return render(request, "home_patron.html", {"user": user})  # 일반 사용자 화면

def landing(request):
        return render(request, "landing/landing.html")  # 사서 화면
    
def login_cancelled(request):
    return render(request, "account/login.html")

def login_cancelled_3rdparty(request):
    return render(request, "account/login.html")
