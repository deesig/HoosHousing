from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leasing_service.models import LeaseRequest, Lease
from listing_service.models import Property
from notification_service.models import Notification
from datetime import datetime, date
from django.db.models import Q, Case, When, Value, IntegerField

@login_required
def submit_lease_request(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            messages.error(request, "Please provide both start and end dates.")
            return redirect('listing_service:property_details', property_id=property_id)

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start_date_obj >= end_date_obj:
                messages.error(request, "Start date must be before end date.")
                return redirect('listing_service:property_details', property_id=property_id)
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return redirect('listing_service:property_details', property_id=property_id)
            
        existing_request = LeaseRequest.objects.filter(
            user=request.user, 
            property=property_instance
        ).first()
        
        if existing_request:
            if existing_request.status in ['denied', 'approved']:
                existing_request.status = 'requested'
                existing_request.start_date = start_date_obj
                existing_request.end_date = end_date_obj
                existing_request.save()
                messages.success(request, "Your lease request has been resubmitted.")
            else:
                messages.error(request, "You already have a lease request for this property.")
            return redirect('listing_service:property_details', property_id=property_id)
        
        LeaseRequest.objects.create(
            user=request.user,
            property=property_instance,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status="requested"
        )
        
        messages.success(request, "Your lease request has been submitted.")
        return redirect('listing_service:property_details', property_id=property_id)

    return redirect('listing_service:property_details', property_id=property_id)


@login_required
def manage_lease_requests(request):
    if request.user.role != 'librarian':
        messages.error(request, "You do not have permission to manage lease requests.")
        return redirect('listing_service:collection_listing')

    # search query
    q = request.GET.get('q', '').strip()

    lease_requests = LeaseRequest.objects.all()

    if request.method == "POST":
        lease_request_id = request.POST.get("lease_request_id")
        action = request.POST.get("action")
        lease_request = get_object_or_404(LeaseRequest, id=lease_request_id)

        if action == "approve":
            Lease.objects.create(
                user=lease_request.user,
                property=lease_request.property,
                start_date=lease_request.start_date,
                end_date=lease_request.end_date,
            )
            lease_request.status = "approved"
            lease_request.save()

            lease_request.property.status = 'leased'
            lease_request.property.save()

            Notification.objects.create(
                user=lease_request.user,
                message=f"Your lease request for {lease_request.property.title} has been approved.",
                notification_type=Notification.lease,
                status=Notification.approved
            )

            other_requests = LeaseRequest.objects.filter(
                property=lease_request.property,
                status='requested'
            ).exclude(id=lease_request.id)
            
            for other_request in other_requests:
                other_request.status = 'denied'
                other_request.save()
                
                Notification.objects.create(
                    user=other_request.user,
                    message=f"Your lease request for {lease_request.property.title} has been denied because another request was approved.",
                    notification_type=Notification.lease,
                    status=Notification.denied
                )
            
            if other_requests.exists():
                messages.success(request, f"Lease request for {lease_request.property.title} has been approved. All other pending requests for this property have been denied.")
            else:
                messages.success(request, f"Lease request for {lease_request.property.title} has been approved.")
                
        elif action == "deny":
            lease_request.status = "denied"
            lease_request.save()
            
            Notification.objects.create(
                user=lease_request.user,
                message=f"Your lease request for {lease_request.property.title} has been denied.",
                notification_type=Notification.lease,
                status=Notification.denied
            )
            
            messages.success(request, f"Lease request for {lease_request.property.title} has been denied.")

    base_qs = LeaseRequest.objects.all()
    if q:
        base_qs = base_qs.filter(
            Q(user__username__icontains=q) |
            Q(property__title__icontains=q)
        )

    pending_requests = base_qs.filter(status='requested') \
        .annotate(
        action_priority=Case(
            When(status='requested', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('action_priority', 'start_date', '-created_at')

    history_requests = base_qs.exclude(status='requested') \
        .order_by('-updated_at')

    return render(request, 'leasing_service/manage_lease_requests.html', {
        'pending_requests': pending_requests,
        'history_requests': history_requests,
        'q': q,
    })



@login_required
def my_leases(request):
    leases = Lease.objects.filter(user=request.user).select_related('property')

    for lease in leases:
        if lease.end_date == date.today():
            lease.property.status = 'available'
            lease.property.save()

            lease.delete()
            messages.success(request, f"The lease for '{lease.property.title}' has been canceled due to expiration.")
            Notification.objects.create(
                    user=request.user,
                    message=f"Your lease for {lease.property.title} has expired.",
                    notification_type=Notification.lease,
                    status=Notification.denied
                )

    leases = Lease.objects.filter(user=request.user).select_related('property')
    lease_requests = LeaseRequest.objects.filter(user=request.user, status='requested')


    return render(request, 'leasing_service/my_leases.html', {'leases': leases, 'lease_requests': lease_requests})


@login_required
def cancel_lease(request, lease_id):
    lease = get_object_or_404(Lease, id=lease_id, user=request.user)

    property_instance = lease.property
    property_instance.status = 'available'
    property_instance.save()

    lease.delete()

    messages.success(request, f"The lease for '{property_instance.title}' has been canceled.")
    return redirect('leasing_service:my_leases')
