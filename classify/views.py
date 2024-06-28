import os
import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import URLForm, RegisterForm, WhitelistForm
from classify.models import Hosts, Whitelist
from classify.classify import final_classification
from classify.saveword import analyze_and_store_full_sentence, save_keywords_to_category_tables
from asgiref.sync import sync_to_async
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib import messages

import asyncio


def run_spider(url):
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'config.settings'

    scrapy_project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_words')

    if not os.path.exists(scrapy_project_path):
        raise FileNotFoundError(f"Scrapy project path does not exist: {scrapy_project_path}")

    process = subprocess.Popen(['scrapy', 'crawl', 'getwords', '-a', f'start_url={url}'],
                               cwd=scrapy_project_path,
                               env=env)
    process.wait()


async def process_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            # 화이트리스트 체크
            if await sync_to_async(Whitelist.objects.filter(url=url).exists)():
                return JsonResponse({"status": "success", "classification": "정상"},
                                    json_dumps_params={'ensure_ascii': False})

            host_instance, created = await Hosts.objects.aget_or_create(host=url)
            should_classify = False

            if created or host_instance.last_check_time is None:
                host_instance.create_time = timezone.now()
                should_classify = True
            else:
                time_difference = timezone.now() - host_instance.last_check_time
                if time_difference.days >= 7:
                    should_classify = True

            if should_classify:
                run_spider(url)
                await analyze_and_store_full_sentence(host_instance)
                classification = await final_classification(host_instance)
                host_instance.classification = classification
                host_instance.last_check_time = timezone.now()
                # 여기서 redirect_url을 갱신합니다.
                redirect_url = await sync_to_async(get_redirect_url)(host_instance.host)
                if redirect_url:
                    host_instance.redirect = redirect_url
                await sync_to_async(host_instance.save)()
            else:
                classification = host_instance.classification

            await save_keywords_to_category_tables()

            return JsonResponse({"status": "success", "classification": classification},
                                json_dumps_params={'ensure_ascii': False})
    else:
        form = URLForm()
    return render(request, 'classify/url_form.html', {'form': form})


async def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            category = form.cleaned_data['category']
            host_instance, created = await Hosts.objects.aget_or_create(host=url)
            host_instance.classification = category
            host_instance.create_time = timezone.now()
            host_instance.last_check_time = timezone.now()
            await sync_to_async(host_instance.save)()

            run_spider(url)
            await analyze_and_store_full_sentence(host_instance)
            await save_keywords_to_category_tables()

            return JsonResponse({"status": "success", "message": "URL registered and keywords saved successfully"},
                                json_dumps_params={'ensure_ascii': False})
    else:
        form = RegisterForm()
    return render(request, 'classify/register.html', {'form': form})



class WhitelistView(FormView):
    template_name = 'classify/whitelist.html'
    form_class = WhitelistForm
    success_url = reverse_lazy('whitelist')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'URL has been added to the whitelist successfully.')
        return super().form_valid(form)


def get_redirect_url(host):
    # 이 함수는 host에 해당하는 리다이렉트 URL을 반환하는 함수입니다.
    # 구체적인 구현은 필요에 따라 다를 수 있습니다.
    # 예시:
    try:
        host_instance = Hosts.objects.get(host=host)
        return host_instance.redirect
    except Hosts.DoesNotExist:
        return None
