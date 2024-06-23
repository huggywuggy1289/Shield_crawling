import sys
import json
from flask import Flask, request, jsonify, render_template
from multiprocessing import Process, Manager
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from pasing import KeywordSpider
from scrapy.utils.log import configure_logging

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
    data = request.get_json()
    url = data.get('url')
    depth = int(data.get('depth', 5))

    manager = Manager()
    results = manager.list()  # 공유 리스트 생성

    # Scrapy 스파이더를 별도의 프로세스로 실행
    p = Process(target=run_spider, args=(url, depth, results))
    p.start()
    p.join()

    # 크롤링 결과 응답
    formatted_results = [{
        'success': item['success'],
        'id': item['id'],
        'url': item['url'],
        'malicious': item['malicious']
    } for item in results]

    return jsonify(formatted_results)

def run_spider(url, depth, results):
    configure_logging()
    process = CrawlerProcess(settings)
    process.crawl(KeywordSpider, start_url=url, depth=depth, results=results)
    process.start()  # This will block until the crawling is finished

if __name__ == '__main__':
    app.run(debug=True)














