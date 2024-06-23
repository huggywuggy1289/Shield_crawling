import scrapy
from scrapy import Selector
from urllib.parse import urlparse, urljoin, unquote
from collections import deque
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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

from classify.models import Hosts


class GeturlsSpider(scrapy.Spider):
    name = "geturls"
    handle_httpstatus_list = [403]  # HTTP 403 상태 코드를 처리하도록 설정

    def __init__(self, *args, **kwargs):
        super(GeturlsSpider, self).__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.depth_limit = 5  # 기본값으로 초기화

        # 큐를 인자로 받아서 초기화
        queue_json = kwargs.get('queue')
        self.queue = deque(json.loads(queue_json))

        # 초기 큐 상태 로그
        self.log(f"Initial queue: {self.queue}", level=logging.INFO)

        self.visited_urls = set()
        self.visited_hosts = set()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GeturlsSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.depth_limit = crawler.settings.getint('DEPTH_LIMIT', 5)  # 설정에서 깊이 제한 읽기
        return spider

    def start_requests(self):
        while self.queue:
            url, depth = self.queue.popleft()
            self.log(f"Popped from queue: {url} at depth {depth}", level=logging.INFO)
            yield scrapy.Request(url, meta={'depth': depth}, callback=self.parse)

    async def parse(self, response):
        if response.status == 403:
            self.log(f"Access denied to {response.url}", level=logging.WARNING)
            return

        current_url = response.url
        current_depth = response.meta['depth']

        if current_depth > self.depth_limit:
            return

        self.driver.get(current_url)
        html = self.driver.page_source
        response = Selector(text=html)

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
            url = unquote(url)

            if url not in self.visited_urls:
                self.visited_urls.add(url)
                host = self.extract_host(url)

                # 데이터베이스에서 호스트 존재 여부 확인
                if not await self.async_host_exists_in_db("https://" + host + "/"):
                    if host not in self.visited_hosts:
                        self.visited_hosts.add(host)
                        await self.async_store_host_in_db("https://" + host + "/")
                        self.log(f"Added to database: {host}", level=logging.INFO)
                    self.queue.append((url, current_depth + 1))
                    self.log(f"Added to queue: {url}", level=logging.INFO)

        if self.queue:
            next_url, next_depth = self.queue[0]
            yield scrapy.Request(next_url, meta={'depth': next_depth}, callback=self.parse)
        else:
            self.driver.quit()

    def extract_onclick_urls(self, response):
        # Onclick 이벤트에서 URL 추출
        onclick_urls = []
        onclick_elements = response.css('[onclick]')
        for elem in onclick_elements:
            onclick_content = elem.attrib['onclick']
            # URL을 추출하는 로직을 구현해야 합니다.
            # 예를 들어, onclick="window.location.href='https://example.com'"과 같은 경우를 처리할 수 있습니다.
            # 이를 파싱하여 URL을 추출해야 합니다.
            # 아래는 간단한 예시입니다:
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
