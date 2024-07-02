from django.core.paginator import Paginator
import os
import subprocess
from collections import Counter
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils import timezone
from asgiref.sync import sync_to_async
from .forms import URLForm, RegisterForm, WhitelistForm
from .models import Hosts, WordCount, Whitelist, ReportUrl
from classify.classify import final_classification
from classify.saveword import analyze_and_store_full_sentence, save_keywords_to_category_tables
from datetime import datetime, timedelta
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

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

async def url_form(request):
    total_hosts = await sync_to_async(Hosts.objects.count)()
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    total_today = await sync_to_async(Hosts.objects.filter(create_time__date=today).count)()
    total_yesterday = await sync_to_async(Hosts.objects.filter(create_time__date=yesterday).count)()

    return render(request, 'classify/url_form.html', {
        'total_hosts': total_hosts,
        'total_today': total_today,
        'total_yesterday': total_yesterday
    })

async def search(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            return redirect(f'/classify/search/?url={url}')
    else:
        url = request.GET.get('url')
        if not url:
            return redirect('url_form')

        host_instance = await process_url_logic(url)
        word_counts = await sync_to_async(lambda: list(WordCount.objects.filter(host=host_instance).order_by('-count')[:5]))()
        keywords = [wc.words for wc in word_counts]

        # Report URL 가져오기 및 페이지네이션 처리
        report_urls = await sync_to_async(lambda: list(ReportUrl.objects.filter(url=host_instance).order_by('-create_at')))()
        paginator = Paginator(report_urls, 10)  # 페이지 당 10개의 항목
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'classify/search.html', {
            'host': host_instance,
            'keywords': keywords,
            'page_obj': page_obj,
            'total_reports': paginator.count
        })

async def report(request):
    if request.method == 'POST':
        reported_url = request.POST.get('reported-url')
        report_tag = request.POST.get('report-tag')
        other_tag = request.POST.get('other-tag')
        report_reason = request.POST.get('report-reason')

        # URL 유효성 검사
        url_validator = URLValidator()
        try:
            url_validator(reported_url)
        except ValidationError:
            messages.error(request, "유효한 URL을 입력하세요.")
            return render(request, 'classify/report.html')

        # 신고 내용 저장
        host_instance, _ = await Hosts.objects.aget_or_create(host=reported_url)
        await sync_to_async(host_instance.save)()  # 저장하여 인스턴스가 데이터베이스에 저장되도록 함
        report_url = ReportUrl(url=host_instance, tag=report_tag if report_tag != '기타' else other_tag,
                               reason=report_reason)
        await sync_to_async(report_url.save)()

        # final 필드 업데이트
        report_tags = await sync_to_async(
            lambda: list(ReportUrl.objects.filter(url=host_instance).values_list('tag', flat=True)))()
        tags = report_tags + [host_instance.classification]

        most_common_tag = Counter(tags).most_common(1)[0][0]
        if most_common_tag in ['도박사이트', '성인사이트', '불법저작물배포사이트', '기타', '정상']:
            host_instance.final = most_common_tag
        else:
            host_instance.final = '기타'

        await sync_to_async(host_instance.save)()

        messages.success(request, "신고가 성공적으로 접수되었습니다.")
        return redirect(reverse('search') + f'?url={reported_url}')
    return render(request, 'classify/report.html')


async def process_url_logic(url):
    # 화이트리스트 체크
    if await sync_to_async(Whitelist.objects.filter(url=url).exists)():
        host_instance, _ = await Hosts.objects.aget_or_create(host=url, defaults={'classification': '정상'})
        host_instance.final = '정상'
        await sync_to_async(host_instance.save)()
        return host_instance

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
        redirect_url = await sync_to_async(get_redirect_url)(host_instance.host)
        if redirect_url:
            host_instance.redirect = redirect_url
        await sync_to_async(host_instance.save)()
    else:
        classification = host_instance.classification

    await save_keywords_to_category_tables()
    await sync_to_async(host_instance.save)()  # 인스턴스를 데이터베이스에 저장

    # Hosts 모델의 final 필드 업데이트
    report_tags = await sync_to_async(lambda: list(ReportUrl.objects.filter(url=host_instance).values_list('tag', flat=True)))()
    tags = report_tags + [host_instance.classification]

    most_common_tag = Counter(tags).most_common(1)[0][0]
    if most_common_tag in ['도박사이트', '성인사이트', '불법저작물배포사이트', '기타', '정상']:
        host_instance.final = most_common_tag
    else:
        host_instance.final = '기타'

    await sync_to_async(host_instance.save)()

    return host_instance

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
    try:
        host_instance = Hosts.objects.get(host=host)
        return host_instance.redirect
    except Hosts.DoesNotExist:
        return None
