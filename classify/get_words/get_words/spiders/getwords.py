import scrapy
from scrapy.selector import Selector
from get_words.items import GetWordsItem
from scrapy.http import Request
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pytesseract
import re
from io import BytesIO
from PIL import Image, ImageSequence
import os
from collections import Counter

class GetwordsSpider(scrapy.Spider):
    name = "getwords"

    def __init__(self, start_url=None, *args, **kwargs):
        super(GetwordsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.extracted_words = []
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/opt/tesseract/share/tessdata/'

    def parse(self, response):
        original_url = self.start_urls[0]
        redirected_url = response.url

        texts = self.extract_with_scrapy(response)
        self.extracted_words.extend(texts)

        # if len(self.extracted_words) < 100:
        #     texts = self.extract_with_selenium(response.url)
        #     self.extracted_words.update(texts)

        if len(self.extracted_words) < 1:
            texts = self.extract_with_proxies(response.url)
            self.extracted_words.extend(texts)

        if len(self.extracted_words) > 10000:
            self.extracted_words = list(self.extracted_words)[:10000]

        full_sentence = ' '.join(self.extracted_words)
        item = GetWordsItem()
        item['host'] = original_url
        item['redirect_url'] = redirected_url if redirected_url != original_url else None
        item['full_sentence'] = full_sentence
        yield item

    def extract_with_scrapy(self, response):
        cleaned_html = re.sub(r'<(script|style|meta|link).*?>.*?</\1>', '', response.text, flags=re.DOTALL)
        cleaned_html = re.sub(r'<!--.*?-->', '', cleaned_html, flags=re.DOTALL)
        selector = Selector(text=cleaned_html)
        texts = selector.css('body *::text').getall()
        cleaned_texts = [word for text in texts for word in self.clean_text(text)]
        return cleaned_texts

    def extract_with_selenium(self, url):
        try:
            options = Options()
            options.add_argument("headless")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            body_element = driver.find_element(By.TAG_NAME, 'body')
            body_text = body_element.text
            body_words = re.findall(r'\b\w+\b', body_text)

            all_tags = driver.find_elements(By.XPATH, '//*[@content]')
            contents = [tag.get_attribute("content") for tag in all_tags]
            contents_words = []
            for content in contents:
                content_word = re.findall(r'[\uAC00-\uD7A3]+', content)
                contents_words.extend(content_word)

            combined_list = body_words + contents_words
            return combined_list

        except Exception as e:
            self.logger.error(f"Error extracting with Selenium: {e}")
            return []

        finally:
            driver.quit()

    def clean_text(self, text):
        text = re.sub(r'[^\w\s]', ' ', text)
        words = re.findall(r'\b\w+\b', text)
        return words

    def extract_in_image(self, response, original_url):
        img_urls = response.css('img::attr(src), img::attr(data-original), img::attr(data-src)').extract()
        for img_url in img_urls:
            if not img_url.startswith(('http', 'https')):
                img_url = urljoin(response.url, img_url)
            yield Request(img_url, callback=self.parse_image, meta={'img_url': img_url, 'original_url': original_url})

    def parse_image(self, response):
        img_url = response.meta['img_url']
        original_url = response.meta['original_url']
        redirected_url = response.url

        try:
            img = Image.open(BytesIO(response.body))
            if img.format not in ['JPEG', 'PNG', 'GIF']:
                return

            min_image_width = 50
            min_image_height = 50
            width, height = img.size

            if width > min_image_width and height > min_image_height:
                if img.format == 'GIF':
                    frames = ImageSequence.Iterator(img)
                    for frame in frames:
                        last_frame = frame
                    text = pytesseract.image_to_string(last_frame, lang='kor+eng')
                else:
                    text = pytesseract.image_to_string(img, lang='kor+eng')

                gettext = self.process_text(text)
                if gettext:
                    count_words = self.extract_words_count(gettext)

                    self.extracted_words.update(gettext)
                    if len(self.extracted_words) > 10000:
                        self.extracted_words = list(self.extracted_words)[:10000]

                    full_sentence = ' '.join(self.extracted_words)
                    item = GetWordsItem()
                    item['host'] = original_url
                    item['redirect_url'] = redirected_url if redirected_url != original_url else None
                    item['full_sentence'] = full_sentence
                    yield item
        except Exception as e:
            self.logger.error(f"Error parsing image: {e}")
            return

    def process_text(self, text):
        text = re.sub(r'\b[ㄱ-ㅎㅏ-ㅣ]\b', '', text)
        text = re.sub('[0-9]', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'\s+', ' ', text)
        word_list = text.strip().split()
        cleaned_word_list = [re.sub(r'[ㄱ-ㅎㅏ-ㅣ]', '', word) for word in word_list]
        filtered = [word for word in cleaned_word_list if len(word) > 1]
        return filtered

    def extract_words_count(self, words):
        return dict(Counter(words))

    def extract_with_proxies(self, url):
        proxy_list = [
            '84.252.73.132:4444',
            '62.236.76.83:8085',
            '91.92.155.207:3128',
            '72.10.164.178:25371',
            '65.109.179.27:80',
            '65.109.189.49:80',
            '125.77.25.178:8090',
            '34.148.178.57:4444',
            '64.227.4.244:8888',
            '67.43.236.19:3397',
            '67.43.236.20:31979',
            '125.77.25.177:8080',
            '185.105.91.62:4444',
            '51.158.169.52:29976',
            '47.56.110.204:8989',
            '91.107.147.205:80',
            '139.162.78.109:8080',
            '111.160.204.146:9091',
            '185.222.115.104:31280',
            '188.132.209.245:80',
            '67.43.227.226:32847',
            '20.235.159.154:80',
            '135.181.154.225:80',
            '72.10.164.178:5313',
            '51.195.40.90:80',
            '221.140.235.236:5002',
            '152.26.229.86:9443',
            '72.10.160.171:8465',
            '35.185.196.38:3128',
            '203.57.51.53:80',
            '103.86.109.38:80',
            '51.89.14.70:80',
            '51.254.78.223:80',
            '12.186.205.122:80',
            '154.85.58.149:80',
            '103.49.202.252:80',
            '185.105.89.249:4444',
            '79.174.12.190:80',
            '103.198.26.22:80',
            '34.23.45.223:80',
            '72.10.160.90:21403',
            '203.89.8.107:80',
            '123.30.154.171:7777'
        ]

        for proxy in proxy_list:
            try:
                # 프록시를 사용하는 새로운 Request 객체 생성
                request = Request(url=url, callback=self.extract_with_scrapy,
                                  meta={'proxy': proxy})
                # Request 객체를 다운로드하고, 결과를 받아 처리
                texts = self.crawler.engine.download(request, self)
                if texts and len(texts) > 0:
                    self.extracted_words.update(texts)
                    if len(self.extracted_words) > 0:
                        return self.extracted_words
            except Exception as e:
                self.logger.error(f"Proxy {proxy} failed: {e}")
                continue
        return []

