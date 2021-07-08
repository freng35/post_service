from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Profile


class AddCommentForm(forms.Form):
    comment = forms.CharField(max_length=500,
                              required=True,
                              widget=forms.Textarea(attrs={
                                  'placeholder': 'Ваш комментарий',
                                  'style': 'width: 90%;'
                              }))


class ProfileUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = False

    class Meta:
        model = Profile
        fields = ('job', 'biography', 'gender', 'country', 'birth')


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name' )
#'email'

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not User.objects.filter(email=email).exists():
            return email
        else:
            raise forms.ValidationError("Email is already in use!")
