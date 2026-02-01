from django.shortcuts import render


import os

from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q

from advertisements.models import Advertisement

TEMPLATE_DIR = 'advertisements'

def home(request):
    context = {
        'title': 'Домашняя страница',
        'heading': 'Добро пожаловать на сайт!',
        'content': 'Это контент домашней страницы',
    }
    return render(request, 'diplom/home.html', context)
def about(request):
    return render(request, 'about.html')
def contact(request):
    return render(request, 'contact.html')

# Create your views here.
class AdvertisementsUserListView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy('account_login')

    def get_queryset(self):
        return Advertisement.objects.for_user(self.request.user)
