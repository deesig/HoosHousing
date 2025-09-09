from django.utils.text import get_valid_filename
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notification_service.models import Notification

from user_service.views import guest_or_login_required, not_guest
from .models import PROXIMITY_CHOICES, REGION_CHOICES, CollectionAccess, CollectionProperty, Property, Collection
from django.shortcuts import get_object_or_404
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_GET
import requests
from review_service.models import Review
from leasing_service.models import Lease
from django.db.models import Avg, Q, Case, When, Value, IntegerField, Count
from django.db import models
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
import boto3
from django.http import JsonResponse
import uuid
import mimetypes

# Create your views here.
# helper function for geocode
def geocode_address(address):
    try:
        # timeout as 4 seconds and set user_agent
        geolocator = Nominatim(user_agent="myApp", timeout=4)
        location = geolocator.geocode(address)

        if location:
            return {
                'lat': location.latitude,
                'lon': location.longitude
            }
        else:
            return {'lat': None, 'lon': None}

    except (GeocoderUnavailable, GeocoderTimedOut) as e:
        return {'lat': None, 'lon': None}
    except Exception as e:
        return {'lat': None, 'lon': None}


@require_GET
def get_walk_score(request, property_id):
    try:
        property_object = get_object_or_404(Property, id=property_id)
        location = geocode_address(property_object.location)

        if not location['lat'] or not location['lon']:
            return JsonResponse({'error': 'Location could not be geocoded'}, status=400)

        latitude, longitude = location['lat'], location['lon']

        base_url = "https://api.walkscore.com/score"
        params = {
            'format': 'json',
            'lat': latitude,
            'lon': longitude,
            'address': property_object.location,
            'transit': '1',
            'bike': '1',
            'wsapikey': settings.WALKSCORE_API_KEY
        }

        try:
            # Make API request
            response = requests.get(base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            # get the walk, bike, transit scores
            walkscore = data.get('walkscore', None)
            bikescore = data.get('bike', {}).get('score', None)
            transitscore = data.get('transit', {}).get('score', None)
            return JsonResponse({
                'walkscore': walkscore,
                'bikescore': bikescore,
                'transitscore': transitscore,
                'descripton': data.get('description', '')
            })
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Add property
@login_required
def add_property(request):
    if request.user.role != 'librarian':
        return redirect(request.META.get('HTTP_REFERER', 'listing_service:property_listing'))

    if request.method == 'POST':
        title = request.POST['title']
        property_type = request.POST['property_type']
        description = request.POST['description']
        location = request.POST['location']
        price = request.POST['price']
        region = request.POST.get('region', '')
        proximity = request.POST.get('proximity', '')
        image = request.FILES.get('image')
        status = request.POST.get('status', 'available')

        property_object = Property.objects.create(
            title=title,
            property_type=property_type,
            description=description,
            location=location,
            price=price,
            region=region,
            proximity=proximity,
            owner=request.user,
            image=None,
            status=status,
        )

        if image:
            s3_storage = S3Boto3Storage()
            file_name = f"listing-image/{property_object.id}_{image.name}"
            saved_file_path = s3_storage.save(file_name, ContentFile(image.read()))

            property_object.image = f"{settings.AWS_S3_CUSTOM_DOMAIN}/{saved_file_path}"
            property_object.save()

        return redirect('listing_service:property_listing')

    return render(request, 'listing_service/add_property.html')


@login_required
def edit_property(request, property_id):
    if request.user.role != 'librarian':
        messages.error(request, "You don't have permission to edit this property")
        return redirect('listing_service:property_listing')

    property_obj = get_object_or_404(Property, id=property_id)
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        property_obj.title = request.POST['title']
        property_obj.property_type = request.POST['property_type']
        property_obj.description = request.POST['description']
        property_obj.location = request.POST['location']
        property_obj.price = request.POST['price']
        property_obj.region = request.POST.get('region', '')
        property_obj.proximity = request.POST.get('proximity', '')

        image = request.FILES.get('image')
        if image:
            s3_storage = S3Boto3Storage()
            safe_name = get_valid_filename(image.name)
            file_name = f"listing-image/{property_obj.id}_{safe_name}"
            saved_file_path = s3_storage.save(file_name,ContentFile(image.read()))
            property_obj.image = (f"{settings.AWS_S3_CUSTOM_DOMAIN}/{saved_file_path}")
            property_obj.save()

        property_obj.save()
        messages.success(request, f"Property '{property_obj.title}' has been updated successfully.")
        if next_url and next_url not in ('None', ''):
            return redirect(next_url)
        return redirect(f"{ reverse('listing_service:property_listing') }?edit_mode=true")


    context = {
        'property': property_obj,
        'is_edit': True,
        'next': next_url,
    }
    return render(request, 'listing_service/add_property.html', context)


@login_required
def delete_property(request, property_id):
    if request.user.role != 'librarian':
        messages.error(request, "You don't have permission to delete this property.")
        return redirect(request.META.get('HTTP_REFERER', reverse('listing_service:property_listing')))
    
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        property_title = property_obj.title

        Review.objects.filter(property=property_obj).delete()
        CollectionProperty.objects.filter(property=property_obj).delete()

        property_obj.delete()

        messages.success(request, f"Property '{property_title}' has been deleted successfully.")
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(reverse('listing_service:property_listing') + '?edit_mode=true')

    context = {
        'is_edit': True
    }
    return render(request, 'listing_service/property_listing.html', context)

@guest_or_login_required
def property_listing(request):
    query       = request.GET.get("q", "")
    selected_types       = request.GET.getlist("types")
    selected_regions     = request.GET.getlist("regions")
    selected_proximities = request.GET.getlist("proximities")

    qs = Property.objects.all()
    if request.user.role != 'librarian':
        accessible_collections = CollectionAccess.objects.filter(
            user=request.user,
            status='approved'
        ).values_list('collection_id', flat=True)

        qs = qs.filter(
            Q(private_collection__isnull=True) |
            Q(private_collection__private=False) |  
            Q(private_collection__id__in=accessible_collections)
        )

    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    
    if selected_types and "all" not in selected_types:
        qs = qs.filter(property_type__in=selected_types)

    if selected_regions and "all" not in selected_regions:
        qs = qs.filter(region__in=selected_regions)

    if selected_proximities and "all" not in selected_proximities:
        qs = qs.filter(proximity__in=selected_proximities)

    base_fields = [
      ('title', 'Alphabetical'),
      ('price', 'Price'),
      ('id',    'Date Added'),
    ]
    sort_options = []
    for field,label in base_fields:
        sort_options.append(( field,       label, '↑'))
        sort_options.append(( f'-{field}', label, '↓'))

    sort = request.GET.get('sort', '-id')
    allowed = [opt[0] for opt in sort_options]
    if sort in allowed:
        qs = qs.order_by(sort)
    else:
        qs = qs.order_by('-id')

    properties = qs.annotate(
        average_rating=Avg('review__rating'),
        review_count=Count('review')
    )
    for p in properties:
        p.average_rating = round(p.average_rating, 1) if p.average_rating is not None else "N/A"

    context = {
        "properties":       properties,
        "query":            query,
        "type_choices":     [(pt,pt) for pt,_ in Property._meta.get_field('property_type').choices],
        "region_choices":   REGION_CHOICES,
        "proximity_choices":PROXIMITY_CHOICES,
        "selected_types":   selected_types,
        "selected_regions": selected_regions,
        "selected_proximities": selected_proximities,
        "sort":             sort,
        "sort_options":     sort_options,
    }
    return render(request, 'listing_service/property_listing.html', context)


@guest_or_login_required
def property_details(request, property_id):
    property_object = get_object_or_404(Property, id=property_id)

    if property_object.is_private:
        allowed = False
        if request.user.is_authenticated:
            allowed = any([
                request.user == property_object.owner,
                request.user.role == 'librarian',
                property_object.private_collection.user_has_access(request.user)
            ])

        if not allowed:
            messages.error(request, "You don't have permission to view this private property")
            return redirect('listing_service:property_listing')

    location = geocode_address(property_object.location)

    # easter egg
    is_easter = False

    if not location['lat'] or not location['lon']:
        # easter egg for invalid road
        location['lat'], location['lon'] = 39.560500, -107.294140
        is_easter = True
        # return (JsonResponse({'error': 'Location could not be geocoded'}, status=400))

    is_leased = property_object.status == 'leased'

    # only need the dates, the user that requested it is irrelevant
    # Lease object is a guarenteed lease that is APPROVED, so only need date
    user_leases = Lease.objects.filter(property=property_object).values('start_date', 'end_date').distinct()
    leased_dates = [
        {"start": lease['start_date'].isoformat(),
         "end": lease['end_date'].isoformat()}
        for lease in user_leases
    ]

    print(leased_dates)

    details = {
        "id": property_object.id,
        "title": property_object.title,
        "image": property_object.image if property_object.image else "",
        "owner": property_object.owner,
        "property_type": property_object.property_type,
        "region": property_object.get_region_display(),
        "proximity": property_object.get_proximity_display(),
        "description": property_object.description,
        "location": property_object.location,
        "price": property_object.price,
        "lat": location['lat'],
        "lon": location['lon'],
        "review_range": range(1, 6),
        "is_leased": is_leased,
        "leased_dates": leased_dates,
        "easter": is_easter
    }

    reviews = Review.objects.filter(property=property_object).select_related("user")
    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    average_rating = round(average_rating, 1) if average_rating else "N/A"

    rating_choices = [round(x * 0.5, 1) for x in range(2, 11)]

    reviews = Review.objects.filter(property=property_object).select_related("user")

    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = reviews.get(user=request.user)
        except Review.DoesNotExist:
            user_review = None

        reviews = reviews.annotate(
            is_mine=Case(
                When(user=request.user, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('is_mine', '-id')
    else:
        reviews = reviews.order_by('-id')


    return render(
        request,
        "listing_service/property_details.html",
        {
            "details": details,
            "reviews": reviews,
            "average_rating": average_rating,
            "rating_choices": rating_choices,
            "user_review": user_review,
        },
    )


@login_required
def create_collection(request):
    if request.user.role == 'guest':
        messages.error(request, "Guest users cannot create collections.")
        return redirect('listing_service:collection_listing')

    back_url = request.META.get('HTTP_REFERER', reverse('listing_service:collection_listing'))

    # search query
    property_q = request.GET.get('property_q', '').strip()

    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        private = request.POST.get('private') == 'on'
        property_ids = request.POST.getlist('properties')
        image = request.FILES.get('image')

        collection_object = Collection.objects.create(
            title=title,
            description=description,
            private=private,
            owner=request.user,
            image=None
        )

        if image:
            s3_storage = S3Boto3Storage()
            file_name = f"collection-image/{collection_object.id}_{image.name}"
            saved_file_path = s3_storage.save(file_name, ContentFile(image.read()))

            collection_object.image = f"{settings.AWS_S3_CUSTOM_DOMAIN}/{saved_file_path}"
            collection_object.save()

        properties = Property.objects.filter(id__in=property_ids)
        valid_properties = []

        for property in properties:
            if private and property.private_collection:
                messages.error(request, f"Property '{property.title}' is already in a private collection")
                continue

            valid_properties.append(property)

            if private:
                CollectionProperty.objects.filter(property=property).update(hidden=True)
                property.private_collection = collection_object
                property.save()

            CollectionProperty.objects.create(
                collection=collection_object,
                property=property,
                hidden=False
            )

        collection_object.properties.set(valid_properties)

        return redirect('listing_service:my_collections')

    available_properties = Property.objects.exclude(
        collection__private=True
    )
    if property_q:
        available_properties = available_properties.filter(
            title__icontains=property_q
        )

    return render(request, 'listing_service/create_collection.html', {
        'properties': available_properties,
        'property_q': property_q,
        'next': back_url,
        'is_edit': False,
        'edit_mode': False,
        'selected_property_ids': [],
        'back_url': back_url,
    })

@guest_or_login_required
def collection_listing(request):
    collections = Collection.objects.all()

    if not request.user.is_authenticated or request.user.role == "guest":
        collections = collections.filter(private=False)

    base_fields = [
        ('title', 'Alphabetical'),
        ('id',    'Date Created'),
    ]
    sort_options = []
    for field, label in base_fields:
        sort_options.append((field,       label, '↑'))
        sort_options.append((f'-{field}', label, '↓'))

    sort = request.GET.get('sort', '-id')
    allowed = [opt[0] for opt in sort_options]
    if sort in allowed:
        collections = collections.order_by(sort)
    else:
        collections = collections.order_by('-id')

    next_url = request.get_full_path()

    query = request.GET.get('q')
    if query:
        collections = collections.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    collection_access = {}
    if request.user.is_authenticated:
        for collection in collections:
            collection_access[collection.id] = {
                'has_access': collection.user_has_access(request.user),
                'has_requested': collection.user_has_requested_access(request.user),
            }

    return render(request, 'listing_service/collection_listing.html', {
        'collections':      collections,
        'collection_access':collection_access,
        'next_url':         next_url,
        'sort_options':     sort_options,
        'sort':             sort,
    })


def collection_details(request, collection_id):
    collection_object = get_object_or_404(Collection, id=collection_id)

    patrons_with_access = CollectionAccess.objects.filter(collection=collection_object, status='approved').select_related('user')

    from_my_collections = False
    if request.GET.get('from') == 'my_collections':
        from_my_collections = True

    if request.user.is_authenticated and request.user.role == 'librarian':
        # get visible properties
        visible_collection_properties = collection_object.visible_properties()

        property_ids = [cp.property_id for cp in visible_collection_properties]
        properties_with_ratings = Property.objects.filter(id__in=property_ids).annotate(
            average_rating=Avg('review__rating'),
            review_count=models.Count('review')
        )

        property_ratings = {p.id: {'avg': p.average_rating, 'count': p.review_count} for p in properties_with_ratings}

        # attach ratings to the visible properties
        for cp in visible_collection_properties:
            rating_data = property_ratings.get(cp.property_id, {'avg': None, 'count': 0})
            cp.property.average_rating = round(rating_data['avg'], 1) if rating_data['avg'] is not None else "N/A"
            cp.property.review_count = rating_data['count']

        return render(request, 'listing_service/collection_details.html', {
            'collection': collection_object,
            'visible_properties': visible_collection_properties,
            'from_my_collections': from_my_collections,
            'patrons_with_access': patrons_with_access
        })

    if collection_object.private and not collection_object.user_has_access(request.user):
        messages.error(request, "You do not have permission to view this private collection.")
        return redirect('listing_service:collection_listing')

    # get visible properties
    visible_collection_properties = collection_object.visible_properties()

    property_ids = [cp.property_id for cp in visible_collection_properties]
    properties_with_ratings = Property.objects.filter(id__in=property_ids).annotate(
        average_rating=Avg('review__rating'),
        review_count=models.Count('review')
    )

    property_ratings = {p.id: {'avg': p.average_rating, 'count': p.review_count} for p in properties_with_ratings}

    # attach ratings to the visible properties
    for cp in visible_collection_properties:
        rating_data = property_ratings.get(cp.property_id, {'avg': None, 'count': 0})
        cp.property.average_rating = round(rating_data['avg'], 1) if rating_data['avg'] is not None else "N/A"
        cp.property.review_count = rating_data['count']

    return render(request, 'listing_service/collection_details.html', {
        'collection': collection_object,
        'visible_properties': visible_collection_properties,
        'from_my_collections': from_my_collections,
    })

@user_passes_test(not_guest)
def my_collections(request):
    collections = Collection.objects.filter(owner=request.user)
    
    base_fields = [
        ('title', 'Alphabetical'),
        ('id',    'Date Created'),
    ]
    sort_options = []
    for field, label in base_fields:
        sort_options.append((field,       label, '↑'))
        sort_options.append((f'-{field}', label, '↓'))

    sort = request.GET.get('sort', '-id')
    allowed = [opt[0] for opt in sort_options]
    if sort in allowed:
        collections = collections.order_by(sort)
    else:
        collections = collections.order_by('-id')

    query = request.GET.get('q')

    edit_mode = request.GET.get('edit_mode') == 'true'

    next_url = request.get_full_path()

    if query:
        collections = collections.filter(
            models.Q(title__icontains=query) | models.Q(description__icontains=query)
        )

    return render(request, 'listing_service/my_collections.html', {
        'collections': collections,
        'edit_mode': edit_mode,
        'next_url': next_url,
        'sort_options': sort_options,
        'sort': sort,
    })


@login_required
def request_collection_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if collection.user_has_access(request.user):
        messages.info(request, "You already have access to this collection.")
        return redirect('listing_service:collection_listing')

    access_request, created = CollectionAccess.objects.get_or_create(
        collection=collection,
        user=request.user,
        defaults={'status': 'requested'}
    )

    if not created and access_request.status == 'denied':
        access_request.status = 'requested'
        access_request.save()
        messages.success(request, f"Access request for '{collection.title}' has been renewed.")
    else:
        messages.success(request, f"Access requested for '{collection.title}'.")

    return redirect('listing_service:collection_listing')


@login_required
def manage_access_requests(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        access_request = get_object_or_404(CollectionAccess, id=request_id)

        if action == 'approve':
            access_request.status = 'approved'
            access_request.save()
            messages.success(request,
                             f"Access granted to {access_request.user} for '{access_request.collection.title}'.")
            Notification.objects.create(
                user=access_request.user,
                message=f"Your access request for {access_request.collection.title} has been approved.",
                notification_type=Notification.collection,
                status=Notification.approved
            )
                             
        elif action == 'deny':
            access_request.status = 'denied'
            access_request.save()
            messages.success(request,
                             f"Access denied to {access_request.user} for '{access_request.collection.title}'.")
            Notification.objects.create(
                user=access_request.user,
                message=f"Your access request for {access_request.collection.title} has been denied.",
                notification_type=Notification.collection,
                status=Notification.denied
            )

        return redirect('listing_service:manage_access_requests')

    # owned_collections = Collection.objects.filter(owner=request.user, private=True)

    pending_requests = CollectionAccess.objects.filter(collection__in=Collection.objects.all(), status='requested').select_related('user', 'collection')

    return render(request, 'listing_service/manage_access_requests.html', {'pending_requests': pending_requests})

@login_required
def revoke_collection_access(request, collection_id, user_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if request.user != collection.owner and request.user.role != 'librarian':
        messages.error(request, "You do not have permission to revoke access.")
        return redirect('listing_service:collection_details', collection_id=collection_id)
    access = get_object_or_404(CollectionAccess, collection=collection, user_id=user_id, status='approved')
    access.status = 'denied'
    access.save()
    messages.success(request, f"Access revoked for {access.user.get_full_name() or access.user.username}.")
    return redirect('listing_service:collection_details', collection_id=collection_id)

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.user != collection.owner and request.user.role != 'librarian':
        messages.info(request, "You do not have access to delete this collection.")
        return redirect('listing_service:collection_listing')

    next_url  = request.GET.get('next') or reverse('listing_service:my_collections')
    edit_mode = request.GET.get('edit_mode') == 'true'

    if request.method == 'POST':
        collection_title = collection.title

        if collection.private:

            collection_properties = CollectionProperty.objects.filter(collection=collection)

            for cp in collection_properties:

                prop = cp.property
                prop.private_collection = None
                prop.save()

                CollectionProperty.objects.filter(property=prop).update(hidden=False)

        collection.delete()

        messages.success(request, f"Collection '{collection_title}' has been deleted successfully.")
        redirect_to = next_url
        if edit_mode:
            sep = '&' if '?' in next_url else '?'
            redirect_to = f"{next_url}{sep}edit_mode=true"
        return redirect(redirect_to)

    return render(request, 'listing_service/confirm_delete_collection.html', {
      'collection': collection,
      'next':       next_url,
      'edit_mode':  edit_mode,
    })

@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.user != collection.owner and request.user.role != 'librarian':
        messages.info(request, "You do not have access to edit this collection.")
        return redirect('listing_service:collection_listing')

    next_url = (
        request.GET.get('next')
        or request.POST.get('next')
        or reverse('listing_service:collection_listing')
    )

    edit_mode = (request.GET.get('edit_mode') == 'true' or request.POST.get('edit_mode') == 'true')

    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        private = request.POST.get('private') == 'on'
        property_ids = request.POST.getlist('properties')

        edit_mode = request.POST.get('edit_mode') == 'true'
        
        # update title/description
        collection.title = title
        collection.description = description

        # detect a public→private flip
        was_private = collection.private
        collection.private = private
        
        if (
            not was_private and        # it was public
            private and                # now turning private
            request.user.role == 'librarian' and
            collection.owner != request.user
        ):
            collection.owner = request.user

        collection.save()

        new_properties = Property.objects.filter(id__in=property_ids)

        current_property_ids = collection.properties.values_list('id', flat=True)

        properties_to_add = [p for p in new_properties if p.id not in current_property_ids]

        properties_to_remove = collection.properties.exclude(id__in=property_ids)

        image = request.FILES.get('image')
        if image:
            s3_storage = S3Boto3Storage()
            file_name = f"collection-image/{collection.id}_{image.name}"
            saved_file_path = s3_storage.save(file_name, ContentFile(image.read()))
            collection.image = f"{settings.AWS_S3_CUSTOM_DOMAIN}/{saved_file_path}"
            collection.save()

        if not was_private and private:
            for prop in new_properties:
                if prop.private_collection and prop.private_collection != collection:
                    messages.error(request, f"Property '{prop.title}' is already in another private collection.")
                    continue

                prop.private_collection = collection
                prop.save()
                CollectionProperty.objects.filter(property=prop).exclude(collection=collection).update(hidden=True)

        elif was_private and not private:
            for prop in collection.private_properties.all():
                prop.private_collection = None
                prop.save()
                # Unhide in all collections
                CollectionProperty.objects.filter(property=prop).update(hidden=False)

        for prop in properties_to_remove:
            CollectionProperty.objects.filter(collection=collection, property=prop).delete()

            if was_private and prop.private_collection == collection:
                prop.private_collection = None
                prop.save()
                # Unhide in all other collections
                CollectionProperty.objects.filter(property=prop).update(hidden=False)

        for prop in properties_to_add:
            if private and prop.private_collection and prop.private_collection != collection:
                messages.error(request, f"Property '{prop.title}' is already in another private collection.")
                continue

            CollectionProperty.objects.create(
                collection=collection,
                property=prop,
                hidden=False
            )

            if private:
                prop.private_collection = collection
                prop.save()
                CollectionProperty.objects.filter(property=prop).exclude(collection=collection).update(hidden=True)

        messages.success(request, f"Collection '{collection.title}' has been updated successfully.")

        redirect_to = next_url
        if edit_mode:
            sep = '&' if '?' in next_url else '?'
            redirect_to = f"{next_url}{sep}edit_mode=true"
        return redirect(redirect_to)

    if collection.private:
        available_properties = Property.objects.filter(
            Q(private_collection__isnull=True) | Q(private_collection=collection)
        )
    else:
        available_properties = Property.objects.exclude(
            Q(private_collection__isnull=False) & ~Q(private_collection=collection)
        )

    selected_property_ids = collection.properties.values_list('id', flat=True)

    if edit_mode:
        sep     = '&' if '?' in next_url else '?'
        back_url = f"{next_url}{sep}edit_mode=true"
    else:
        back_url = next_url

    return render(request, 'listing_service/create_collection.html', {
        'collection': collection,
        'properties': available_properties,
        'selected_property_ids': selected_property_ids,
        'is_edit': True,
        'edit_mode': edit_mode,
        'next': next_url,
        'back_url': back_url,
    })

@guest_or_login_required
def search_properties(request):
    query = request.GET.get('q', '').strip()

    qs = Property.objects.all()

    if request.user.role != 'librarian':
        qs = qs.exclude(collection__private=True)

    if query:
        qs = qs.filter(title__icontains=query)

    data = {
        "properties": [
            {
                "id": property.id,
                "title": property.title,
            }
            for property in qs
        ]
    }
    return JsonResponse(data)

@require_GET
def get_presigned_url(request):
    extension = request.GET.get('extension', 'jpg')


    allowed_extensions = ['jpg', 'jpeg', 'png']
    if extension.lower() not in allowed_extensions:
        return JsonResponse({'error': 'File type not allowed.'}, status=400)

    content_type, _ = mimetypes.guess_type(f"file.{extension}")

    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                      region_name=settings.AWS_S3_REGION_NAME)

    file_name = f"collections/{uuid.uuid4()}.{extension}"
    presigned_post = s3.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_name,
        Fields={"acl": "public-read", "Content-Type": content_type},
        Conditions=[
            {"acl": "public-read"},
            {"Content-Type": content_type}
        ],
        ExpiresIn=3600
    )
    return JsonResponse({
        'url': presigned_post['url'],
        'fields': presigned_post['fields'],
        'full_url': f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_name}"
    })
