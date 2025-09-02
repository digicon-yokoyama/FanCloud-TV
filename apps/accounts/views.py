from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .models import User, UserProfile
from django import forms


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('streaming:home')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('streaming:home')
    http_method_names = ['get', 'post', 'options']
    
    def get(self, request, *args, **kwargs):
        """Allow GET requests for logout."""
        return self.post(request, *args, **kwargs)


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password2 = forms.CharField(label='パスワード確認', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("パスワードが一致しません")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(user=user)
        return user


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('streaming:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        user = authenticate(
            username=user.username,
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        messages.success(self.request, 'アカウントが作成されました！')
        return response


@login_required
def profile(request):
    """User profile page."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update from modal form
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile.bio = request.POST.get('bio', profile.bio)
        profile.website = request.POST.get('website', profile.website)
        profile.save()
        
        messages.success(request, 'プロフィールが更新されました')
        return redirect('accounts:profile')
    
    context = {
        'profile': profile,
        'user_videos': [],  # Add video queryset here when Video model is ready
        'user_playlists': [],  # Add playlist queryset here when Playlist model is ready
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def settings(request):
    """User settings page."""
    if request.method == 'POST':
        # Handle settings update
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile = user.profile
        profile.bio = request.POST.get('bio', profile.bio)
        profile.website = request.POST.get('website', profile.website)
        profile.twitter = request.POST.get('twitter', profile.twitter)
        profile.youtube = request.POST.get('youtube', profile.youtube)
        profile.save()
        
        messages.success(request, '設定が更新されました')
        return redirect('accounts:settings')
    
    context = {
        'user': request.user,
        'profile': getattr(request.user, 'profile', None),
    }
    return render(request, 'accounts/settings.html', context)