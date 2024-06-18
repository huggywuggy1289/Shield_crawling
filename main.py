import sys
import json
import threading
from flask import Flask, request, jsonify, render_template
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pasing import KeywordSpider  # 파일 이름에 맞게 수정하세요

app = Flask(__name__)

# Scrapy 설정 가져오기
settings = get_project_settings()
settings.set('FEEDS', {
    'output.json': {'format': 'json'},
})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-crawl', methods=['POST'])
def start_crawl():
    url = request.json.get('url')
    depth = int(request.json.get('depth', 5))
    results = []

    # 스크래피 스파이더 실행 스레드 시작
    thread = threading.Thread(target=run_spider, args=(url, depth, results))
    thread.start()
    thread.join()  # 스레드 종료 대기

    # 크롤링 결과 응답
    formatted_results = [{
        'success': item['success'],
        'id': item['id'],
        'url': item['url'],
        'malicious': item['malicious']
    } for item in results]

    return jsonify(formatted_results)

# Scrapy 크롤러를 직접 실행하는 함수
def run_spider(url, depth, results):
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': 'output.json'  # 파일을 직접 저장할 경로
    })
    process.crawl(KeywordSpider, start_url=url, depth=depth, results=results)
    process.start()

if __name__ == '__main__':
    app.run(debug=True)




