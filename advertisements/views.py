from django.shortcuts import render


import os

from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.db.models import Q

from advertisements.models import Advertisement
from diplom import settings

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

class AdvertisementDetailView(DetailView):
    login_url = reverse_lazy('account_login')
    model = Advertisement


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        advertisement = self.object
        context['image'] = advertisement.image_url
        context['title'] = advertisement.title
        context['category'] = advertisement.category
        context['author_id'] = advertisement.author
        context['description'] = advertisement.description
        return context

class AdvertisementCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy('account_login')
    model = Advertisement
    fields = [
        'image_url',
        'title',
        'category',
        'description',
        'price',
        'location',
    ]

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('advertisements')

class AdvertisementDeleteView(LoginRequiredMixin, DeleteView):
    login_url = reverse_lazy('account_login')
    model = Advertisement
    success_url = reverse_lazy('advertisements')

    def get_queryset(self):
        return Advertisement.objects.for_user(self.request.user)

class AdvertisementUpdateView(LoginRequiredMixin, UpdateView):
    login_url = reverse_lazy('account_login')
    model = Advertisement
    fields = [
        'image_url',
        'title',
        'category',
        'description',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update advertisement'
        return context

    def get_success_url(self):
        return reverse('advertisements')


class HomePageView(TemplateView):
    template_name = os.path.join('advertisements', 'advertisement_list.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем все объявления
        advertisements = Advertisement.objects.all()

        # Настройка пагинации (10 объявлений на страницу)
        paginator = Paginator(advertisements, settings.PAGE_ENTITY)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['advertisements'] = page_obj
        context['paginator'] = paginator
        context['page_obj'] = page_obj

        return context


class SearchResultsView(ListView):
    model = Advertisement
    context_object_name = 'advertisements'
    paginate_by = settings.PAGE_ENTITY  # 10 объявлений на страницу

    def get_queryset(self):
        query = self.request.GET.get('q')
        clear = self.request.GET.get('clear')

        if clear == 'true':
            return Advertisement.objects.all()

        if query:
            return Advertisement.objects.filter(
                Q(title__icontains=query)
            )
        return Advertisement.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
