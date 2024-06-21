import os
import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import URLForm
from classify.models import Host
from classify.classify import analyze_and_store_full_sentence, final_classification
from asgiref.sync import sync_to_async

# 스크래피를 실행하여 URL에서 단어를 추출하는 함수
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

# URL을 처리하고 분류 결과를 반환하는 함수
async def process_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            host_instance, created = await Host.objects.aget_or_create(host=url)
            should_classify = False

            # 새로 생성된 경우 또는 마지막 검사 시간이 없는 경우
            if created or host_instance.last_check_time is None:
                host_instance.create_time = timezone.now()
                should_classify = True
            else:
                # 마지막 검사로부터 7일이 지난 경우
                time_difference = timezone.now() - host_instance.last_check_time
                if time_difference.days >= 7:
                    should_classify = True

            if should_classify:
                # 스크래피를 실행하여 단어를 추출
                run_spider(url)
                # 추출된 단어를 분석하고 저장
                await analyze_and_store_full_sentence(host_instance)
                # 최종 분류를 결정
                classification = await final_classification(host_instance)
                # 분류 결과와 마지막 검사 시간을 업데이트
                host_instance.classification = classification
                host_instance.last_check_time = timezone.now()
                await sync_to_async(host_instance.save)()
            else:
                classification = host_instance.classification

            return JsonResponse({"status": "success", "classification": classification}, json_dumps_params={'ensure_ascii': False})
    else:
        form = URLForm()
    return render(request, 'classify/url_form.html', {'form': form})
