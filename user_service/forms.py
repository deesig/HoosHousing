from allauth.account.forms import SignupForm
from allauth.account.forms import LoginForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSignupForm(SignupForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, label="First Name", required=True)
    last_name = forms.CharField(max_length=30, label="Last Name", required=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please log in instead.")
        return email
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.save()
        return user
    
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         self.fields['login'].label = ""
         self.fields['password'].label = ""
