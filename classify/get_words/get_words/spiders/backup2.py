import pytesseract
import re
import scrapy
from io import BytesIO
from PIL import Image, ImageSequence
from scrapy.http import Request
from urllib.parse import urljoin
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
from get_words.items import GetWordsItem

class GetwordsSpider(scrapy.Spider):
    name = "getwords33"

    def __init__(self, start_url=None, *args, **kwargs):
        super(GetwordsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.use_proxy = False

        # Mac용 Tesseract 경로 설정
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/opt/tesseract/share/tessdata/'

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, errback=self.errback, meta={'original_url': url}, dont_filter=True)

    def parse(self, response):
        original_url = response.meta['original_url']
        redirected_url = response.url

        # 로그 추가
        self.logger.info(f"Original URL: {original_url}")
        self.logger.info(f"Redirected URL: {redirected_url}")

        texts = self.extract_with_scrapy(response)
        total_words = set(texts)

        if len(total_words) < 100:
            texts.extend(self.extract_with_selenium(redirected_url))

        if len(total_words) < 100 and not self.use_proxy:
            # 프록시를 사용하여 다시 시도
            self.use_proxy = True
            yield Request(original_url, callback=self.parse, errback=self.errback,
                          meta={'original_url': original_url, 'proxy': True}, dont_filter=True)
        else:
            image_texts = list(self.extract_in_image(response, redirected_url))
            for future in image_texts:
                res = yield future
                if res and 'gettext' in res.meta:
                    texts.extend(res.meta['gettext'])

            full_sentence = ' '.join(texts)

            item = GetWordsItem()
            item['host'] = original_url  # 원래 URL을 호스트로 설정
            item['redirect_url'] = redirected_url if isinstance(redirected_url, str) and redirected_url != original_url else None
            item['full_sentence'] = full_sentence
            yield item

    def extract_with_selenium(self, url):
        try:
            self.logger.info(f"Starting Selenium extraction for URL: {url}")
            options = Options()
            options.add_argument("headless")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            all_tags = driver.find_elements(By.XPATH, '//*[@content]')
            contents = [tag.get_attribute("content") for tag in all_tags if tag.get_attribute("content")]
            contents_words = []
            for content in contents:
                content_word = re.findall(r'[\uAC00-\uD7A3]+', content)
                contents_words.extend(content_word)

            body_element = driver.find_element(By.TAG_NAME, 'body')
            body_text = body_element.text
            body_words = re.findall(r'\b\w+\b', body_text)
            combined_list = body_words + contents_words

            self.logger.info(f"Selenium extraction completed for URL: {url}")

            return combined_list

        except Exception as e:
            self.logger.error(f"Error during Selenium extraction for URL: {url} - {str(e)}")
            return []

        finally:
            driver.quit()

    def extract_with_scrapy(self, response):
        cleaned_html = re.sub(r'<(script|style).*?>.*?</\1>', '', response.text, flags=re.DOTALL)
        selector = Selector(text=cleaned_html)
        texts = selector.css('body *::text').getall()
        cleaned_texts = [word for text in texts for word in self.clean_text(text)]
        self.logger.info(f"Scrapy extraction found {len(cleaned_texts)} words")
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
                    existing_item = next((item for item in self.crawler.engine.scraper.slot.active if item['host'] == original_url), None)
                    if existing_item:
                        existing_item['full_sentence'] += ' ' + ' '.join(gettext)
                    else:
                        item = GetWordsItem()
                        item['host'] = original_url
                        if isinstance(redirected_url, str) and redirected_url != original_url:
                            item['redirect_url'] = redirected_url
                        else:
                            item['redirect_url'] = None
                        item['full_sentence'] = ' '.join(gettext)
                        yield item
        except Exception as e:
            self.logger.error(f"Error processing image from URL: {img_url} - {str(e)}")
            return

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

    def errback(self, failure):
        original_url = failure.request.meta['original_url']
        self.logger.error(f"Request failed for URL: {original_url} - {failure.value}")
        self.save_failed_url(original_url)

    def save_failed_url(self, url):
        item = GetWordsItem()
        item['host'] = url
        item['redirect_url'] = None
        item['full_sentence'] = ''
        self.crawler.engine.scraper.itemproc.process_item(item, self)
