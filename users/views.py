import os

from django.views.generic import UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

from advertisements.models import Advertisement
from users.models import User


# Create your views here.
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User

    template_name = os.path.join('users', 'profile.html')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        advertisements = Advertisement.objects.filter(author=self.object).order_by('-created_at')
        context['image'] = user.image_url
        context['username'] = user.username
        context['email'] = user.email
        context['first_name'] = user.first_name
        context['last_name'] = user.last_name
        context['advertisements'] = advertisements
        return context

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'image_url']
    template_name = os.path.join('users', 'profile_update.html')
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        return self.request.user == user

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = os.path.join('users', 'profile_confirm_delete.html')
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        return self.request.user == user
