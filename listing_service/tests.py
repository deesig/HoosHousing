from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from listing_service.models import Property, Collection, CollectionAccess

class UserProfileViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.client = Client()
        User = get_user_model()

        # Create a patron user
        self.user = User.objects.create_user(
            username='patron', 
            email='patron@example.com',
            password='patronpassword123',
            role='patron' # Ensure user is patron
        )

        # Create a librarian user
        self.librarian = User.objects.create_user(
            username='librarian',
            email='librarian@gmail.com',
            password='librarianpassword123',
            role='librarian' # Ensure user is librarian
        )
        
        # Create a guest user
        self.guest = User.objects.create_user(
            username='guest',
            email='guest@gmail.com',
            role='guest' # Ensure user is guest
        )

        # URLs to test
        self.view_property_list_url = reverse('listing_service:property_listing')
        self.add_property_url = reverse('listing_service:add_property')
        self.login_url = reverse('account_login')
    
    # Test: Guest account creation (Special), no password
    def test_guest_user_creation(self):
        guest = get_user_model().objects.get(username='guest')
        self.assertEqual(guest.role, 'guest')
        self.assertFalse(guest.has_usable_password())
        self.assertTrue(guest.is_guest)
    
    # Test: Property listing view should be accessible to all guests, patrons, librarians
    # NOT accessible to unauthenticated users
    """
        Test that the property listing view is accessible to all guests, patrons, librarians,
        excluding unauthenticated users.
    """
    def test_property_listing_view_not_accessible_to_all(self):
        
        # Unauthenticated user (non guest)
        response = self.client.get(self.view_property_list_url)
        self.assertEqual(response.status_code, 302) # Should NOT be accessible to unauthenticated user

    def test_property_listing_view_guest(self):
        # Guest user
        self.client.force_login(self.guest)
        response = self.client.get(self.view_property_list_url)
        self.assertEqual(response.status_code, 200) # Should be accessible to guest users
        
    def test_property_listing_view_patron(self):
        # Patron user
        self.client.login(username='patron', password='patronpassword123')
        response = self.client.get(self.view_property_list_url)
        self.assertEqual(response.status_code, 200)  # Should be accessible to patron users

    def test_property_listing_view_librarian(self):
        # Librarian user
        self.client.login(username='librarian', password='librarianpassword123')
        response = self.client.get(self.view_property_list_url)
        self.assertEqual(response.status_code, 200)  # Should be accessible to librarian users


    # Test: Add property view only works for librarians
        """
        Test that the add property view behaves correctly based on user roles:
        - Unauthenticated users should be redirected.
        - Patron users should be redirected.
        - Librarian users should be able to access the view.
        """
        # Unauthenticated user: add property view does NOT work
    def test_all_users_add_property_view(self):
        response = self.client.get(self.add_property_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code

        # Patron: add property view does NOT work
    def test_patron_add_property_view(self):
        self.client.login(username='patron', password='patronpassword123')
        response = self.client.get(self.add_property_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Librarian: add property view DOES work
    def test_librarian_add_property_view(self):
        self.client.login(username='librarian', password='librarianpassword123')
        response = self.client.get(self.add_property_url)
        self.assertEqual(response.status_code, 200)  # Redirect status code
        self.assertTemplateUsed(response, 'listing_service/add_property.html') 
    
    # Test: Create collection only works for patrons and librarians
        """
        Test the create collections view:
        - Unauthenticated users should be redirected.
        - Patron users should be able to access the view.
        - Librarian users should also be able to access the view.
        """
        # Unauthenticated users should NOT be able to create a collection
    def test_unauthenticated_users_create_collection_view(self):
        response = self.client.get(reverse('listing_service:create_collection'))
        self.assertEqual(response.status_code, 302)  # Redirect status code

        # Patrons: can create collections
    def test_patron_create_collection_view(self):
        # Patron user: should be able to access the view
        self.client.login(username='patron', password='patronpassword123')
        response = self.client.get(reverse('listing_service:create_collection'))
        self.assertEqual(response.status_code, 200)  # Should be accessible to patron users
        self.assertTemplateUsed(response, 'listing_service/create_collection.html')

        # Librarian: can create collections
    def test_librarian_create_collection_view(self):
        # Librarian user: should also be able to access the view
        self.client.login(username='librarian', password='librarianpassword123')
        response = self.client.get(reverse('listing_service:create_collection'))
        self.assertEqual(response.status_code, 200)  # Should be accessible to librarian users
        self.assertTemplateUsed(response, 'listing_service/create_collection.html')
        
class CollectionAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()

        # Create users
        self.librarian = User.objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='librarianpass',
            role='librarian'
        )
        
        self.patron = User.objects.create_user(
            username='patron',
            email='patron@example.com',
            password='patronpass',
            role='patron'
        )
        
        self.guest = User.objects.create_user(
            username='guest',
            email='guest@example.com',
            role='guest'
        )

        # Create collection and property
        self.private_collection = Collection.objects.create(
            title="Private Collection",
            private=True,
            owner=self.librarian
        )
        
        self.public_property = Property.objects.create(
            title="Public Property",
            owner=self.librarian,
            location="1815 Jefferson Park Ave",
            price=1000
        )

    # Private Collection Access Tests
    def test_private_collection_guest_access(self):
        """Test guest users cannot access private collections"""
        self.client.force_login(self.guest)
        response = self.client.get(reverse('listing_service:collection_details', args=[self.private_collection.id]))
        self.assertEqual(response.status_code, 302)

    def test_private_collection_patron_access(self):
        """Test patrons without access get redirected from private collections"""
        self.client.login(username='patron', password='patronpass')
        response = self.client.get(reverse('listing_service:collection_details', args=[self.private_collection.id]))
        self.assertEqual(response.status_code, 302)

    def test_access_request_flow(self):
        """Test full access request workflow"""
        # Patron requests access
        self.client.login(username='patron', password='patronpass')
        response = self.client.post(reverse('listing_service:request_collection_access', args=[self.private_collection.id]))
        self.assertRedirects(response, reverse('listing_service:collection_listing'))
        
        # Librarian approves request
        self.client.login(username='librarian', password='librarianpass')
        access_request = CollectionAccess.objects.get(collection=self.private_collection)
        response = self.client.post(reverse('listing_service:manage_access_requests'), {
            'request_id': access_request.id,
            'action': 'approve'
        })
        self.assertRedirects(response, reverse('listing_service:manage_access_requests'))
        
        # Verify patron access
        self.client.login(username='patron', password='patronpass')
        response = self.client.get(reverse('listing_service:collection_details', args=[self.private_collection.id]))
        self.assertEqual(response.status_code, 200)
    #######################
    # below this is WIP 
    #######################
    '''
    # Property Visibility Tests
    def test_private_property_visibility(self):
        """Test private properties are hidden from public listings"""
        # Create private property
        private_property = Property.objects.create(
            title="Private Property",
            owner=self.librarian,
            location="Private Location",
            price=2000,
            private_collection=self.private_collection
        )
        
        # Guest user
        self.client.force_login(self.guest)
        response = self.client.get(reverse('listing_service:property_listing'))
        self.assertNotIn(private_property, response.context['properties'])
        
        # Librarian user (any librarian can access private property)
        self.client.login(username='librarian', password='librarianpass')
        response = self.client.get(reverse('listing_service:property_listing'))
        self.assertIn(private_property, response.context['properties'])

        # Authorized user
        self.client.login(username='patron', password='patronpass')
        self.private_collection.access_permissions.create(user=self.patron, status='approved')
        response = self.client.get(reverse('listing_service:property_listing'))
        self.assertIn(private_property, response.context['properties'])

    # Collection Modification Tests
    def test_collection_edit_permissions(self):
        """Test only owners can edit collections"""
        edit_url = reverse('listing_service:edit_collection', args=[self.private_collection.id])
        
        # Patron user
        self.client.login(username='patron', password='patronpass')
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 302)
        
        # Owner librarian
        self.client.login(username='librarian', password='librarianpass')
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

    def test_collection_deletion(self):
        """Test collection deletion removes associated permissions"""
        delete_url = reverse('listing_service:delete_collection', args=[self.private_collection.id])
        
        # Create access request
        CollectionAccess.objects.create(
            collection=self.private_collection,
            user=self.patron,
            status='approved'
        )
        
        # Delete collection
        self.client.login(username='librarian', password='librarianpass')
        response = self.client.post(delete_url)
        self.assertEqual(CollectionAccess.objects.count(), 0)
        self.assertFalse(Collection.objects.filter(id=self.private_collection.id).exists())

    # Property Detail Tests
    def test_invalid_property_detail_easter_egg(self):
        """Test easter egg location for failed geocoding"""
        invalid_property = Property.objects.create(
            title="Invalid Location",
            owner=self.librarian,
            location="Invalid Address 123",
            price=3000
        )
        
        self.client.force_login(self.guest)
        response = self.client.get(reverse('listing_service:property_details', args=[invalid_property.id]))
        self.assertTrue(response.context['details']['easter'])
        self.assertEqual(response.context['details']['lat'], 39.560500)
        self.assertEqual(response.context['details']['lon'], -107.294140)

    # My Properties View Tests
    def test_my_properties_access(self):
        """Test my_properties view access controls"""
        url = reverse('listing_service:my_properties')
        
        # Guest user
        self.client.force_login(self.guest)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Patron user
        self.client.login(username='patron', password='patronpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Should redirect as non-librarian
        
        # Librarian user
        self.client.login(username='librarian', password='librarianpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
'''