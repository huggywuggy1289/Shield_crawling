import os
import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from .forms import URLForm
from classify.models import Host, WordCount
from classify import classify

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
            existing_host = Host.objects.filter(host=url).first()
            if existing_host and existing_host.classification:
                classification = existing_host.classification
            else:
                run_spider(url)
                # 스크래핑 후 데이터베이스에 기록이 업데이트되었는지 확인
                host, created = Host.objects.get_or_create(host=url)
                top_10_keywords = classify.get_top10_keywords(host)
                classification = classify.classify_site(top_10_keywords)
                host.classification = classification
                host.save()
            return JsonResponse({"status": "success", "classification": classification}, json_dumps_params={'ensure_ascii': False})
    else:
        form = URLForm()
    return render(request, 'classify/url_form.html', {'form': form})
