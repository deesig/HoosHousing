from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("guest", "Guest"),
        ("patron", "Patron"),
        ("librarian", "Librarian"),
    )

    email = models.EmailField(unique=True, blank=False, null=False)
    first_name = models.CharField(max_length=150, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patron")
    profile_image = models.URLField(blank=True, null=True)
    
    def clean(self):
        super().clean()
        if self.email:
            existing = CustomUser.objects.filter(email__iexact=self.email).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'email': 'A user with this email already exists (case-insensitive).'})

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True
    )

    @property
    def is_guest(self):
        return self.role == 'guest' or self.username == 'guest'

    @property
    def is_librarian(self):
        return self.role == 'librarian'