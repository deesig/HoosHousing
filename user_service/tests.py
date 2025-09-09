from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Create your tests here.

class UserProfileViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpassword123'
        )
        
        # URLs to test
        self.edit_profile_url = reverse('user_service:edit_profile')
        self.login_url = reverse('account_login')
        
    # Test: edit profile view requires login   
    def test_edit_profile_view_requires_login(self):
        # Test that profile view redirects to login when not authenticated
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect status code
    
	# Test: edit profile view works when logged in 
    def test_edit_profile_view_when_logged_in(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200) # Success status code
        self.assertTemplateUsed(response, 'user_service/edit_profile.html')
    
	# Test: edit profile username post request
    def test_edit_profile_username_post(self):
        # Log in the test user
        self.client.login(username='testuser', password='testpassword123')
        
		# Test updating username
        update_data = {
            'username': 'bettertestuser'
		}
        
		# Make the POST request to edit_profile
        response = self.client.post(self.edit_profile_url, update_data)
        
		# Redirect after successful update
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertEqual(response.url, self.edit_profile_url) # Check redirect URL stays on same page
        
		# Verify username was updated
        updated_user = get_user_model().objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, 'bettertestuser')