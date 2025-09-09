from django.db import models
from user_service.models import CustomUser

PROPERTY_CHOICES = [
    ('Apartment',   'Apartment'),
    ('Condo',       'Condo'),
    ('Room',        'Room'),
    ('House',       'House'),
    ('Other',       'Other'),
]

REGION_CHOICES = [
    ('central_grounds',     'Central Grounds'),
    ('north_grounds',       'North Grounds'),
    ('rugby_corridor',      'Rugby Road Corridor'),
    ('university_corner',   'West Main / University Corner'),
    ('jpa',                 'Jefferson Park Avenue'),
    ('downtown_mall',       'Downtown Mall / City Center'),
    ('barracks_road',       'Barracks Road Area'),
    ('frys_spring',         'Fry\'s Spring'),
    ('greenbrier',          'Greenbrier / Barracks West'),
    ('pantops',             'Pantops & Meadow Creek'),
    ('shadwell',            'Shadwell & Ivy'),
]

PROXIMITY_CHOICES = [
    ('on_grounds',      'On-Grounds Housing'),
    ('within_0_5_mi',   'Within 0.5 mi of Grounds'),
    ('0_5_to_1_mi',     '0.5-1 mi from Grounds'),
    ('1_to_2_mi',       '1-2 mi from Grounds'),
    ('charlottesville', 'Charlottesville City'),
    ('albemarle',       'Albemarle County'),
]

class Property(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="properties",
        null=True,
        blank=True
    )
    property_type = models.CharField(max_length=50, choices=PROPERTY_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('leased',    'Leased'),
    ], default='available')

    region = models.CharField(
        max_length=30,
        choices=REGION_CHOICES,
        blank=True,
    )
    proximity = models.CharField(
        max_length=20,
        choices=PROXIMITY_CHOICES,
        blank=True,
    )

    private_collection = models.ForeignKey(
        'Collection',
        on_delete=models.SET_NULL,
        null=True,
        related_name='private_properties'
    )

    def __str__(self):
        return self.title

    @property
    def is_private(self):
        return self.private_collection is not None
    
class Collection(models.Model):
    title = models.CharField(max_length=255)
    image = models.URLField(blank=True, null=True)
    properties = models.ManyToManyField(Property, through='CollectionProperty')
    description = models.TextField()
    private = models.BooleanField(default=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)

    def visible_properties(self):
        return CollectionProperty.objects.filter(
            collection=self,
            hidden=False
        ).select_related('property')

    def has_visible_properties(self):
        return self.collectionproperty_set.filter(hidden=False).exists()

    def user_has_access(self, user):
        if not user.is_authenticated:
            return False
        if user == self.owner:
            return True
        if not self.private:
            return True
        return self.access_permissions.filter(user=user, status='approved').exists()

    def user_has_requested_access(self, user):
        if not user.is_authenticated:
            return False
        return self.access_permissions.filter(user=user, status='requested').exists()

    def __str__(self):
        return self.title


class CollectionProperty(models.Model):
    collection = models.ForeignKey('Collection', on_delete=models.CASCADE)
    property = models.ForeignKey('Property', on_delete=models.CASCADE)
    hidden = models.BooleanField(default=False)

    class Meta:
        unique_together = ('collection', 'property')


class CollectionAccess(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='access_permissions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='collection_permissions')
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ], default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('collection', 'user')
