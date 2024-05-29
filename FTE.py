import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import app1
from transformers import pipeline
import whois
from collections import Counter

# 특정 키워드 설정
gambler_keywords = ['도박', '먹튀', '야툰', '스포츠', '일진', '토렌트', '축구', '토토','베팅', '슬롯', '리그','중계중','스포츠중계','토너먼트','고스톱','포커','섯다','맞고','룰렛']
webtoon_keywords = [ '웹툰','야툰','일진','액션물','로맨스','판타지','드라마','BL','GL','만화','웹소설','만화책','동인지','마니아','트레이드']
obscence_keywords = ['성인', '야설', '에로', 'AV', '포르노', '야동', '에로티카', '성인만화', '아다', '포로노그래피', '섹스', '조건만남', '성인물', '음란물', '성인영화']

# 오류가 발생한 URL을 저장할 리스트
failed_urls = []

# Hugging Face에서 제공하는 텍스트 요약 MODEL 추가
summarizer = pipeline("summarization")

# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'

# app1.py에서 스크래핑한  결과를 가져옴
scraped_urls = app1.scrape_urls(base_url, depth=5, timeout_seconds=15)

for url in scraped_urls:
    try:
        # 가져온 url들에 대한 도메인 추출 작업 실행
        domain = urlparse(base_url).netloc
        w = whois.whois(domain)

    except Exception as e:
         print("Error getting WHOIS information:", str(e))


print("모니터링 된 도메인")

print(w)
     
print("----------------------------------------------------------------------------------------------")
# 오류가 발생한 URL 출력
print("\nFailed URLs:")
for url in failed_urls:
    print(url)