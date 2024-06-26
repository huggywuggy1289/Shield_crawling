import random
import time
from flask import Flask, render_template, request, url_for
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote

app = Flask(__name__)

# 프록시 서버 설정
# proxies = {
#     'http': 'http://127.0.0.1:5000/',
#     'https': 'https://127.0.0.1:5000/',
# }

# 스크랩한 URL을 저장할 리스트
scraped_urls = []

def scrape_urls(url):
    # URL에서 HTML 가져오기
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 모든 링크를 찾아서 리스트에 추가
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and (href.startswith('http://') or href.startswith('https://')):
            # URL 인코딩
            href = quote(href, safe='/:?=&%')
            scraped_urls.append(href)
            print(href)  # 수집된 URL 확인
    print(scraped_urls)  # 현재까지 스크랩된 URL 목록 출력

# 방문한 링크를 저장할 집합
visited_urls = set()

def get_random_link(links):
    return random.choice(links)

def getlinks(url, timeout_seconds):
    start_time = time.time()
    while True:

        # 방문한 링크 중 랜덤하게 선택
        random_url = random.choice(list(visited_urls)) if visited_urls else url
        
        try:
            # URL 방문
            response = requests.get(url)
            response.raise_for_status()  # 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')

            # 현재 페이지의 모든 링크 추출
            links = [link.get('href') for link in soup.find_all('a', href=True)]
            
            # 현재 페이지의 URL 추가
            visited_urls.add(random_url)

            # 방문하지 않은 URL 중 랜덤하게 다음 URL 선택
            next_urls = [link for link in links if link not in visited_urls]
            if not next_urls:
                break           
            
            # 랜덤하게 다음 URL 선택
            next_url = random.choice(links)

            # 만약 이동할 URL이 없으면 종료
            if not next_url:
                break
            
            # 선택된 URL 출력
            print("Selected URL:", next_url)
            
            break_time = time.time() - start_time
            if break_time >= timeout_seconds:
                print("일정 시간이 지나 스크래핑을 종료합니다.")
                break

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            break


# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'
timeout_seconds = 10
getlinks(base_url, timeout_seconds)

# 스크래핑할 페이지 수
num_pages_to_scrape = 5

# 지정된 페이지 수만큼 스크랩
for i in range(num_pages_to_scrape):
    print("Scraping URLs for page", i+1)
    scrape_urls(base_url)
    print("URLs scraped for page", i+1, ":", scraped_urls)

    #다음 url선택
    # base_url = getlinks(base_url)
    # if not base_url:
    #     break


@app.route('/')
def index():
    # URL을 디코딩하여 템플릿에 전달
    decoded_urls = [unquote(url) for url in scraped_urls]
    return render_template('index.html', urls=decoded_urls)

@app.route('/result', methods=['POST'])
def result():
    if request.method == 'POST':
        search_query = request.form.get('query', '')
        if not search_query.strip():
            search_results = [] #빈 리스트 할당
        else:
            search_results = [url for url in scraped_urls if search_query in url]
        return render_template('result.html', query=search_query, urls=search_results)
    # else:
    #     return render_template('result.html', query='', urls=[])

if __name__ == '__main__':
    # Flask 애플리케이션 실행
    app.run(debug=True) 








