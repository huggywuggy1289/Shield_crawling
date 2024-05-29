import pandas as pd
# import matplotlib.pyplot as plt
from collections import Counter
import requests
from bs4 import BeautifulSoup

print("한인커뮤니티--------------------------------------------")

url = "https://linkall1.online/bbs/board.php?bo_table=korean&page="

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# <strong> 태그에서 class가 'ellipsis'인 요소 추출
strong_items = soup.find_all('strong')

# 각 요소에서 'a' 태그를 찾아 텍스트 추출하여 출력하기
for strong_tag in strong_items:
    a_tag = strong_tag.find('a', class_='ellipsis')
    if a_tag:
        word = a_tag.get_text(strip=True)
        print(word)

print("드라마--------------------------------------------")

url = "https://linkall1.online/bbs/board.php?bo_table=drama&page="

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# <strong> 태그에서 class가 'ellipsis'인 요소 추출
strong_items = soup.find_all('strong')

# 각 요소에서 'a' 태그를 찾아 텍스트 추출하여 출력하기
for strong_tag in strong_items:
    a_tag = strong_tag.find('a', class_='ellipsis')
    if a_tag:
        word = a_tag.get_text(strip=True)
        print(word)
        
print("커뮤니티--------------------------------------------")

url = "https://linkall1.online/bbs/board.php?bo_table=community&page="

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# <strong> 태그에서 class가 'ellipsis'인 요소 추출
strong_items = soup.find_all('strong')

# 각 요소에서 'a' 태그를 찾아 텍스트 추출하여 출력하기
for strong_tag in strong_items:
    a_tag = strong_tag.find('a', class_='ellipsis')
    if a_tag:
        word = a_tag.get_text(strip=True)
        print(word)
        
print("성인용품--------------------------------------------")

url = "https://linkall1.online/bbs/board.php?bo_table=adultitem&page="

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# <strong> 태그에서 class가 'ellipsis'인 요소 추출
strong_items = soup.find_all('strong')

# 각 요소에서 'a' 태그를 찾아 텍스트 추출하여 출력하기
for strong_tag in strong_items:
    a_tag = strong_tag.find('a', class_='ellipsis')
    if a_tag:
        word = a_tag.get_text(strip=True)
        print(word)

print("성인물--------------------------------------------")

url = "https://linkall1.online/bbs/board.php?bo_table=adult&page="

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# <strong> 태그에서 class가 'ellipsis'인 요소 추출
strong_items = soup.find_all('strong')

# 각 요소에서 'a' 태그를 찾아 텍스트 추출하여 출력하기
for strong_tag in strong_items:
    a_tag = strong_tag.find('a', class_='ellipsis')
    if a_tag:
        word = a_tag.get_text(strip=True)
        print(word)