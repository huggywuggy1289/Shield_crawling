import os
import subprocess
import logging
from django.shortcuts import render
from django.db.models import Q
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from classify.models import Hosts
from classify.saveword import analyze_and_store_full_sentence, save_keywords_to_category_tables
from classify.classify import final_classification
import random


logger = logging.getLogger(__name__)

def start_crawl(request):
    if request.method == 'POST':
        # classification이 NULL이거나 '정상'이 아닌 호스트들 가져오기
        hosts = list(Hosts.objects.filter(Q(classification__isnull=True) | ~Q(classification='정상') | ~Q(classification="알 수 없음")))

        if len(hosts) > 100:
            hosts = random.sample(hosts, 100)

        # 큐 상태 로그
        logger.info(f"Hosts to crawl: {hosts}")
        # Scrapy 스파이더 실행 경로 설정
        scrapy_project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_url')

        for host in hosts:
            # start_url을 인자로 Scrapy 스파이더 실행
            process = subprocess.Popen(['scrapy', 'crawl', 'geturls', '-a', f'start_url={host.host}'], cwd=scrapy_project_path)

            try:
                process.wait()  # Scrapy 스파이더 실행이 완료될 때까지 대기
            except subprocess.CalledProcessError as e:
                logger.error(f"Scrapy process failed with error: {e}")

    return render(request, 'urlcrawl/crawl_url.html')

async def classify_urls(request):
    if request.method == 'POST':
        # last_check_time이 NULL이거나 마지막 검사일이 현재로부터 7일이 넘은 경우 또는 classification이 NULL인 호스트들 가져오기
        hosts = await sync_to_async(list)(Hosts.objects.filter(
            Q(last_check_time__isnull=True) |
            Q(last_check_time__lt=timezone.now() - timedelta(days=7)) |
            Q(classification__isnull=True)
        ))

        if len(hosts) >= 100:
            hosts = hosts[:100]

        for host in hosts:
            await classify_host(host)

        await save_keywords_to_category_tables()

    return render(request, 'urlcrawl/crawl_url.html')

async def classify_host(host_instance):
    url = host_instance.host
    should_classify = False

    if host_instance.last_check_time is None:
        host_instance.created_time = timezone.now()
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

def run_spider(url):
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'config.settings'

    scrapy_project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../classify/get_words')

    if not os.path.exists(scrapy_project_path):
        raise FileNotFoundError(f"Scrapy project path does not exist: {scrapy_project_path}")

    process = subprocess.Popen(['scrapy', 'crawl', 'getwords', '-a', f'start_url={url}'], cwd=scrapy_project_path, env=env)

    try:
        process.wait()  # Scrapy 스파이더 실행이 완료될 때까지 대기
    except subprocess.CalledProcessError as e:
        logger.error(f"Scrapy process failed with error: {e}")

def get_redirect_url(host):
    # 이 함수는 host에 해당하는 리다이렉트 URL을 반환하는 함수입니다.
    # 구체적인 구현은 필요에 따라 다를 수 있습니다.
    # 예시:
    try:
        host_instance = Hosts.objects.get(host=host)
        return host_instance.redirect
    except Hosts.DoesNotExist:
        return None
