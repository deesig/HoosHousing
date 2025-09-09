from django.urls import include, path
from . import views

app_name = 'listing_service'

urlpatterns = [
    path('', views.property_listing, name="property_listing"),
    path('add/', views.add_property, name="add_property"),
    path('property/<int:property_id>/', views.property_details, name='property_details'),
    path('property/<int:property_id>/edit/', views.edit_property, name="edit_property"),
    path('property/<int:property_id>/delete/', views.delete_property, name="delete_property"),
	  path('property/<int:property_id>/walkscore/', views.get_walk_score, name='get_walk_score'),
    path('create/', views.create_collection, name="create_collection"),
    path('collections/', views.collection_listing, name="collection_listing"),
    path('collections/<int:collection_id>/', views.collection_details, name='collection_details'),
    path('collections/<int:collection_id>/edit/', views.edit_collection, name="edit_collection"),
    path('collections/<int:collection_id>/delete/', views.delete_collection, name="delete_collection"),
    path('collections/my_collections/', views.my_collections, name="my_collections"),
    path('collections/request-access/<int:collection_id>/', views.request_collection_access, name='request_collection_access'),
    path('collections/manage-access-requests/', views.manage_access_requests, name='manage_access_requests'),
    path('search_properties/', views.search_properties, name='search_properties'),
    path('collections/<int:collection_id>/revoke_access/<int:user_id>/', views.revoke_collection_access, name='revoke_collection_access'),
    path('get_presigned_url/', views.get_presigned_url, name='get_presigned_url'),
]