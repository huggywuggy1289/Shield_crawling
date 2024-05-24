import time
from bs4 import BeautifulSoup
from requests import request
import requests
import app1
from urllib.parse import urlparse

# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'

# 오류가 발생하는 url을 저장할 리스트
failed_urls = []

# app1.py에서 스크래핑한 결과를 가져옴
scraped_urls = app1.scrape_urls(base_url, depth=5, timeout_seconds=15)


for url in scraped_urls:
    # 출력에 있어 시간제한을 두기 위해
    start_time = time.time()

    try:
         # 가져온 url들에 대한 단어 추출작업 시행
         response = requests.get(url)
         response.raise_for_status() # 문제 발생시 예외처리
         soup = BeautifulSoup(response.text, 'html.parser')
         text = soup.get_text()

         # 텍스트에서 단어 추출
         words = text.split()
         print(words)
        #  if start_time >= 40:
        #       print("단어 추출을 종료합니다.")
        #       break

    except Exception as e:
         print(f"Error fetching {url}: {e}")
         failed_urls.append(url)
         break
