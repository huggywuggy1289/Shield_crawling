import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import app1

# 특정 키워드 설정
malicious_keywords = ['성인', '도박', '먹튀', '야툰', '스포츠', '일진', '토렌트', '축구', '카지노', '토토']

# 오류가 발생한 URL을 저장할 리스트
failed_urls = []

# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'

# app1.py에서 스크래핑한 결과를 가져옴
scraped_urls = app1.scrape_urls(base_url, depth=5, timeout_seconds=15)

for url in scraped_urls:
    try:
        # 가져온 url들에 대한 단어 추출 작업 실행
        response = requests.get(url)
        response.raise_for_status()  # 문제 발생 시 예외 처리
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # 텍스트에서 단어 추출
        words = text.split()
        # print(words)

        for keyword in words:
            # 키워드가 악성 키워드에 포함된다면
            if keyword in malicious_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}")
                break


    except Exception as e:
        print(f"Error fetching {url}: {e}")
        failed_urls.append(url)

# 오류가 발생한 URL 출력
print("\nFailed URLs:")
for url in failed_urls:
    print(url)