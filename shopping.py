import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Chrome() # 크롬 드라이버 경로를 지정해도 됨.
browser.maximize_window() # 창 최대화 옵션

# 스크래핑할 사이트의 URL: 페이지 이동
url = 'https://www.scrapingcourse.com/ecommerce/'
browser.get(url)

# # 조회 항목 초기화
# checkboxes = browser.find_elements(By.NAME, 'fieldIds')
# for checkbox in checkboxes:
#     if checkbox.is_selected():
#         checkbox.click()

# # 조회 항목 설정
# item = ['거래량', '매출액'] # 가져올 리스트 설정
# for checkbox in checkboxes:
#     parent = checkbox.find_element(By.XPATH, '..')
#     label = parent.find_element(By.TAG_NAME, 'label')
#     if label.text in item: # 라벨의 텍스트값이 아이템 리스트에 있다면
#         checkbox.click() # 클릭설정하기
#     print(label.text)
    

# 종목명 가져오기
stock_names =[]

elements = browser.find_elements(By.XPATH, '.woocommerce-loop-product__title')

for element in elements:
    # 종목명이라는 배열에 element의 텍스트요소만 가져와서
    stock_names.append(element.text)
# 출력
print(stock_names)

# 서버 종료시간 늦추기
time.sleep(100)