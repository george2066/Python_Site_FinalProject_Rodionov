import os

from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

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
        context['image'] = user.image_url
        context['username'] = user.username
        context['email'] = user.email
        context['first_name'] = user.first_name
        context['last_name'] = user.last_name
        return context
