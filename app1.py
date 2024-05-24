import random
import time
from weakref import proxy
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urljoin


# 프록시 서버 설정
proxies = {
    "http": "http://127.0.0.1:5000/",
    "https": "https://127.0.0.1:5000/",
}
app = Flask(__name__)

# 스크랩한 URL을 저장할 리스트
scraped_urls = []
visited_urls = set()

# 깊이를 2로 지정함(몇단계까지 따라가는가) / 스크래핑 종료시간 15초
def scrape_urls(url, depth=5, timeout_seconds=15):
    start_time = time.time()
    
    def fetch_links(url):
        try:
            # URL 방문
            response = requests.get(url)
            response.raise_for_status()  # 에러 발생 시 예외 처리
            # url get요청을 받아온 변수의 텍스트만을 출력
            soup = BeautifulSoup(response.text, 'html.parser')

            # 현재 페이지의 모든 링크 추출
            links = [link.get('href') for link in soup.find_all('a', href=True) if link.get('href').startswith('http')]
            return links
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []
        

    # 재귀적 웹페이지 스크래핑(현재 url, 현재 깊이)
    def recursive_scrape(current_url, current_depth):
        # 만약 현재 깊이가 지정 깊이보다 크거나 전체시간-현재시간 값이 지정 시간보다 크다면(지정시간=현재시간이여야함)
        if current_depth > depth or time.time() - start_time >= timeout_seconds:
            # 재귀 호출 종료문으로 리턴값을 아무것도 반환안한다.
            return
        
        print(f"Scraping depth {current_depth}: {current_url}")
        links = fetch_links(current_url)
        visited_urls.add(current_url)
        for link in links:
            absolute_link = urljoin(current_url, link)
            if absolute_link not in visited_urls:
                visited_urls.add(absolute_link)
                scraped_urls.append(quote(absolute_link, safe='/:?=&%'))
                recursive_scrape(absolute_link, current_depth + 1)
    
    recursive_scrape(url, 1)

# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'

# 지정된 페이지 수만큼 스크랩
scrape_urls(base_url, depth=5, timeout_seconds=15)

@app.route('/')
def index():
    return render_template('index.html', urls=scraped_urls)
    # URL을 디코딩하여 템플릿에 전달
    # decoded_urls = [unquote(url) for url in scraped_urls]
    # return render_template('index.html', urls=decoded_urls)

@app.route('/result', methods=['POST'])
def result():
    if request.method == 'POST':
        search_query = request.form.get('query', '')
        if not search_query.strip():
            search_results = []  # 빈 리스트 할당
        else:
            search_results = [url for url in scraped_urls if search_query in url]
        return render_template('result.html', query=search_query, urls=search_results)

if __name__ == '__main__':
    # Flask 애플리케이션 실행
    app.run(debug=True)

