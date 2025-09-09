from django.db import models
from user_service.models import CustomUser

class Notification(models.Model):
    lease = 'lease'
    collection = 'collection'
    other = 'other'
    notification_types = [
        (lease, 'Lease'),
        (collection, 'Collection'),
        (other, 'Other'),
    ]
    approved = 'approved'
    denied = 'denied'
    other = 'other'
    status_choices = [
        (approved, 'Approved'),
        (denied, 'Denied'),
        (other, 'Other'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=10, choices=notification_types, default=other)
    status = models.CharField(max_length=10, choices=status_choices, default=other)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"
