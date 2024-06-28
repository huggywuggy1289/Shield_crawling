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
    name = "getwords22"

    def __init__(self, start_url=None, *args, **kwargs):
        super(GetwordsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]

        # Mac용 Tesseract 경로 설정
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/opt/tesseract/share/tessdata/'


    def start_requests(self):
        for url in self.start_urls:
            yield self.make_request(url)

    def make_request(self, url):
        if self.proxies:
            proxy = self.proxies[self.proxy_index]
            self.logger.info(f"Using proxy: {proxy}")
            return Request(url, callback=self.parse, errback=self.errback, meta={'proxy': f"http://{proxy}", 'original_url': url}, dont_filter=True)
        else:
            self.logger.error("No proxies available.")
            return Request(url, callback=self.parse, errback=self.errback, meta={'original_url': url}, dont_filter=True)

    def parse(self, response):
        original_url = response.meta['original_url']
        redirected_url = response.url

        if response.status == 403:
            self.logger.warning(f"403 Forbidden response for {original_url}. Switching to Selenium.")
            texts = self.extract_with_selenium(original_url)
        else:
            try:
                texts = self.extract_with_scrapy(response)
            except Exception as e:
                self.logger.error(f"Scrapy extraction failed: {e}")
                texts = []

            if len(texts) < 100:
                texts.extend(self.extract_with_selenium(original_url))

        image_texts = list(self.extract_in_image(response, original_url))
        for future in image_texts:
            res = yield future
            if res and 'gettext' in res.meta:
                texts.extend(res.meta['gettext'])

        full_sentence = ' '.join(texts)
        item = GetWordsItem()
        item['host'] = original_url
        item['redirect_url'] = redirected_url if redirected_url != original_url else None
        item['full_sentence'] = full_sentence
        yield item

    def extract_with_selenium(self, url):
        try:
            options = Options()
            options.add_argument("headless")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            all_tags = driver.find_elements(By.XPATH, '//*[@content]')
            contents = [tag.get_attribute("content") for tag in all_tags]
            contents_words = []
            for content in contents:
                content_word = re.findall(r'[\uAC00-\uD7A3]+', content)
                contents_words.extend(content_word)

            body_element = driver.find_element(By.TAG_NAME, 'body')
            body_text = body_element.text
            body_words = re.findall(r'\b\w+\b', body_text)
            combined_list = body_words + contents_words

            return combined_list

        except Exception as e:
            self.logger.error(f"Selenium extraction failed: {e}")
            return []

        finally:
            driver.quit()

    def extract_with_scrapy(self, response):
        cleaned_html = re.sub(r'<(script|style).*?>.*?</\1>', '', response.text, flags=re.DOTALL)
        selector = Selector(text=cleaned_html)
        texts = selector.css('body *::text').getall()
        cleaned_texts = [word for text in texts for word in self.clean_text(text)]
        return cleaned_texts

    def clean_text(self, text):
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
        original_url = response.meta.get('original_url', self.start_urls[0])
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

                    for word, count in count_words.items():
                        item = GetWordsItem()
                        item['host'] = original_url
                        item['redirect_url'] = redirected_url if redirected_url != original_url else None
                        item['full_sentence'] = ' '.join(gettext)
                        yield item
        except Exception as e:
            self.logger.error(f"Image parsing failed: {e}")

    def process_text(self, text):
        text = re.sub(r'\b[ㄱ-ㅎㅏ-ㅣ]\b', '', text)
        text = re.sub('[0-9]', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'\s+', ' ', text)
        word_list = text.strip().split()
        cleaned_word_list = [re.sub(r'[ㄱ-ㅎㅏ-ㅣ]', '', word) for word in word_list]
        filtered = [word for word in cleaned_word_list if len(word) > 1]
        return filtered

    def extract_words_count(self, words):
        return dict(Counter(words))

    def errback(self, failure):
        original_url = failure.request.meta.get('original_url', self.start_urls[0])
        self.logger.error(f"Request failed for {original_url}: {failure.value}")
        self.proxy_index += 1
        if self.proxy_index < len(self.proxies):
            self.logger.info(f"Switching to next proxy: {self.proxies[self.proxy_index]}")
            yield self.make_request(original_url)
        else:
            self.logger.error(f"All proxies failed for {original_url}")
            self.save_failed_url(original_url)

    def save_failed_url(self, url):
        item = GetWordsItem()
        item['host'] = url
        item['redirect_url'] = None
        item['full_sentence'] = ''
        self.crawler.engine.scraper.itemproc.process_item(item, self)
