import os
import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import URLForm
from classify.models import Host, WordCount
from classify.classify import classify_site, get_top10_keywords, update_classification_in_db  # 수정된 부분


def run_spider(url):
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'config.settings'

    # Scrapy 프로젝트 경로를 명확하게 설정
    scrapy_project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_words')

    if not os.path.exists(scrapy_project_path):
        raise FileNotFoundError(f"Scrapy project path does not exist: {scrapy_project_path}")

    process = subprocess.Popen(['scrapy', 'crawl', 'getwords', '-a', f'start_url={url}'],
                               cwd=scrapy_project_path,
                               env=env)
    process.wait()


def process_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            host_instance, created = Host.objects.get_or_create(host=url)
            should_classify = False

            if created:
                host_instance.create_time = timezone.now()
                should_classify = True
            else:
                time_difference = timezone.now() - host_instance.last_check_time
                if time_difference.days >= 7:
                    should_classify = True

            if should_classify:
                run_spider(url)
                top_10_keywords = get_top10_keywords(host_instance)
                if not top_10_keywords:
                    classification = "접속 불가 또는 존재하지않음"
                else:
                    classification = classify_site(top_10_keywords)
                host_instance.classification = classification
                host_instance.last_check_time = timezone.now()
                host_instance.save()
            else:
                classification = host_instance.classification

            return JsonResponse({"status": "success", "classification": classification}, json_dumps_params={'ensure_ascii': False})
    else:
        form = URLForm()
    return render(request, 'classify/url_form.html', {'form': form})
