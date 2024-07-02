import uuid
import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class KeywordSpider(scrapy.Spider):
    name = "keyword_spider"

    custom_settings = {
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, start_url, depth, results, *args, **kwargs):
        super(KeywordSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.depth = depth
        self.visited_urls = set()
        self.scraped_data = results

    def parse(self, response):
        current_depth = response.meta.get('depth', self.depth)
        if response.url in self.visited_urls:
            return
        self.visited_urls.add(response.url)

        self.log(f"Visiting: {response.url} at depth {current_depth}")

        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 텍스트 추출 및 악성 키워드 검사
        text = soup.get_text()
        words = text.split()

        gambler_keywords = ['또또', '온라인슬롯', '도박', '먹튀', '범퍼카', '스포츠', '일진', '토렌트', '축구', '토토', '베팅', '슬롯', '리그', '중계중', '스포츠중계', '토너먼트', '고스톱', '포커', '섯다', '맞고', '룰렛', '카지노', '신규첫충']
        webtoon_keywords = ['야툰', '일진', '액션물', '로맨스', '판타지', '드라마', 'BL', 'GL', '만화', '웹소설', '만화책', '동인지', '마니아', '트레이드', '몰래보기']
        obscence_keywords = ['성인', '야설', '에로', 'AV', '포르노', '야동', '에로티카', '성인만화', '아다', '포로노그래피', '섹스', '조건만남', '성인물', '음란물', '성인영화', 'XVIDEOS', '미미야동', 'AV핑보걸', '리얼타임', 'AV탑걸', '야동공장', 'SIZE19', '색색티비', '야딸두', '야동판', '빨간비디오', '조개파티', '야한티비', '다크걸', 'AV19.org', '망고넷', '코리아섹스비디오']

        malicious = 0  # 0: 정상, 1: 악성
        for word in words:
            if word in gambler_keywords or word in webtoon_keywords or word in obscence_keywords:
                malicious = 1
                break

        # 최종 json형식의 output값:
        self.scraped_data.append({
            'success': 'y', 
            'id': str(uuid.uuid4()),  # 고유 식별자 생성
            'url': response.url,  # 분석된 링크
            'malicious': malicious  # 악성 여부 0:정상 1:악성 2: 접속
        })

        # 링크 추출
        if current_depth > 0:
            for link in soup.find_all('a', href=True):
                absolute_link = urljoin(response.url, link['href'])
                if absolute_link not in self.visited_urls:
                    self.log(f"Found link: {absolute_link} at depth {current_depth - 1}")
                    yield scrapy.Request(absolute_link, callback=self.parse, meta={'depth': current_depth - 1})




