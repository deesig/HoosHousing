from django.db import models
from user_service.models import CustomUser
from listing_service.models import Property

# Create your models here.
class LeaseRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="lease_requests")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="lease_requests")
    start_date = models.DateField(default='0001-01-01')
    end_date = models.DateField(default='9999-12-31')
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ], default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'property')
        verbose_name = "Lease Request"
        verbose_name_plural = "Lease Requests"

    def __str__(self):
        return f"Lease Request by {self.user} for {self.property} - {self.status}"
    
class Lease(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="leases")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="leases")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lease"
        verbose_name_plural = "Leases"

    def __str__(self):
        return f"Lease for {self.property} by {self.user} from {self.start_date} - {self.end_date}"
