import scrapy
from scrapy import Selector
from urllib.parse import urlparse, urljoin, unquote
from collections import deque
import json
import logging

# Django model import
import sys
import os
import django
from asgiref.sync import sync_to_async
from django.utils import timezone

# Django 프로젝트의 절대 경로 설정
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(project_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django를 설정합니다.
django.setup()

from classify.models import Hosts, Whitelist

class GeturlsSpider(scrapy.Spider):
    name = "geturls"
    handle_httpstatus_list = [403]  # HTTP 403 상태 코드를 처리하도록 설정

    def __init__(self, *args, **kwargs):
        super(GeturlsSpider, self).__init__(*args, **kwargs)
        self.depth_limit = 3  # 기본값으로 초기화

        # start_url을 인자로 받아서 초기화
        self.start_url = kwargs.get('start_url')
        self.queue = deque([(self.start_url, 0)])

        # 초기 큐 상태 로그
        self.log(f"Initial queue: {self.queue}", level=logging.INFO)

        self.visited_urls = set()
        self.visited_hosts = set()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GeturlsSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.depth_limit = crawler.settings.getint('DEPTH_LIMIT', 2)  # 설정에서 깊이 제한 읽기
        return spider

    def start_requests(self):
        while self.queue:
            url, depth = self.queue.popleft()
            self.log(f"Popped from queue: {url} at depth {depth}", level=logging.INFO)
            if url:  # Check if url is not None
                yield scrapy.Request(url, meta={'depth': depth}, callback=self.parse, errback=self.errback)

    async def parse(self, response):
        if response.status == 403:
            self.log(f"Access denied to {response.url}", level=logging.WARNING)
            return

        current_url = response.url
        current_depth = response.meta['depth']

        if current_depth > self.depth_limit:
            return

        # URL 추출
        get_urls = response.css('a::attr(href)').extract()
        get_onclick_urls = self.extract_onclick_urls(response)
        all_urls = get_urls + get_onclick_urls

        for url in all_urls:
            if url.startswith('/'):
                url = urljoin(current_url, url)
            elif not url.startswith('http'):
                continue

            # URL을 디코딩하여 잘못된 문자 처리
            url = url.strip()

            host = self.extract_host(url)

            # Whitelist에 있는지 확인
            if await self.async_host_in_whitelist("https://" + host.strip() + "/"):
                self.log(f"Host is in whitelist, skipping: {host}", level=logging.INFO)
                continue

            if url not in self.visited_urls:
                self.visited_urls.add(url)

                # 데이터베이스에서 호스트 존재 여부 확인
                if not await self.async_host_exists_in_db("https://" + host.strip() + "/"):
                    if host not in self.visited_hosts:
                        self.visited_hosts.add(host)
                        await self.async_store_host_in_db("https://" + host.strip() + "/")
                        self.log(f"Added to database: {host}", level=logging.INFO)
                    self.queue.append((url, current_depth + 1))
                    self.log(f"Added to queue: {url}, depth{current_depth + 1}", level=logging.INFO)

        while self.queue:
            next_url, next_depth = self.queue.popleft()
            yield scrapy.Request(next_url, meta={'depth': next_depth}, callback=self.parse, errback=self.errback)

    def extract_onclick_urls(self, response):
        # Onclick 이벤트에서 URL 추출
        onclick_urls = []
        onclick_elements = response.css('[onclick]')
        for elem in onclick_elements:
            onclick_content = elem.attrib['onclick']
            # URL을 추출
            if "window.location.href=" in onclick_content:
                url = onclick_content.split("window.location.href=")[-1].strip("'\" ")
                onclick_urls.append(url)
        return onclick_urls

    def extract_host(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc

    @sync_to_async
    def async_host_exists_in_db(self, host_url):
        return Hosts.objects.filter(host=host_url).exists()

    @sync_to_async
    def async_store_host_in_db(self, host_url):
        Hosts.objects.get_or_create(host=host_url, defaults={'create_time': timezone.now()})

    @sync_to_async
    def async_host_in_whitelist(self, host_url):
        return Whitelist.objects.filter(url=host_url).exists()

    def errback(self, failure):
        self.log(f"Request failed: {failure.request.url}", level=logging.ERROR)
        while self.queue:
            next_url, next_depth = self.queue.popleft()
            yield scrapy.Request(next_url, meta={'depth': next_depth}, callback=self.parse, errback=self.errback)
