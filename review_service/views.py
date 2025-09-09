from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Review
from listing_service.models import Property
from decimal import Decimal
from django.contrib import messages

@login_required
def add_review(request, property_id):
    if request.user.role == "guest":
        messages.error(request, "Guest users cannot submit reviews.")
        return redirect("listing_service:property_details", property_id=property_id)

    if request.method == "POST":
        content = request.POST.get("content")
        rating = request.POST.get("rating")

        try:
            rating = Decimal(rating)
            if rating < 1:
                rating = Decimal("1.0")
        except:
            rating = Decimal("1.0")

        property_obj = get_object_or_404(Property, id=property_id)

        # Check if the user already has a review
        existing = Review.objects.filter(user=request.user, property=property_obj).first()
        if existing:
            # Redirect to edit page instead
            return redirect("review_service:edit_review", review_id=existing.id)

        Review.objects.create(
            user=request.user,
            property=property_obj,
            content=content,
            rating=rating
        )

    return redirect("listing_service:property_details", property_id=property_id)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    property_obj = review.property

    if request.method == "POST":
        review.content = request.POST.get("content", review.content)
        try:
            review.rating = Decimal(request.POST.get("rating", review.rating))
        except:
            pass  # Keep the old rating if conversion fails
        review.save()
        return redirect("listing_service:property_details", property_id=review.property.id)

    return redirect("listing_service:property_details", property_id=review.property.id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.user == request.user:
        review.delete()
    return redirect('listing_service:property_details', property_id=review.property.id)