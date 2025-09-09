from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    user_notifications.update(is_read=True)
    
    return render(request, 'notification_service/notifications.html', {'notifications': user_notifications})

    
