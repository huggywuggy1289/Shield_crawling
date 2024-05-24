import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import app1

# 특정 키워드 설정
gambler_keywords = ['도박', '먹튀', '야툰', '스포츠', '일진', '토렌트', '축구', '토토','베팅', '슬롯', '리그','중계중','스포츠중계','토너먼트','고스톱','포커','섯다','맞고','룰렛']
webtoon_keywords = [ '웹툰','야툰','일진','액션물','로맨스','판타지','드라마','BL','GL','만화','웹소설','만화책','동인지','마니아','트레이드']
obscence_keywords = ['성인', '야설', '에로', 'AV', '포르노', '야동', '에로티카', '성인만화', '아다', '포로노그래피', '섹스', '조건만남', '성인물', '음란물', '성인영화']


# 오류가 발생한 URL을 저장할 리스트
failed_urls = []

# 스크래핑할 사이트의 URL
base_url = 'https://linkall1.online/'

# app1.py에서 스크래핑한 결과를 가져옴
scraped_urls = app1.scrape_urls(base_url, depth=5, timeout_seconds=15)

for url in scraped_urls:
    try:
        # 가져온 url들에 대한 단어 추출 작업 실행
        response = requests.get(url)
        response.raise_for_status()  # 문제 발생 시 예외 처리
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # 텍스트에서 단어 추출
        words = text.split()
        # print(words)

        for keyword in words:
            # 키워드가 악성 키워드에 포함된다면
            if keyword in gambler_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--도박")
            elif keyword in webtoon_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--웹툰")
            elif keyword in obscence_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--성인물")
            else:
                print("정상")

            break


    except Exception as e:
        print(f"Error fetching {url}: {e}")
        failed_urls.append(url)

print("모니터링 된 악성 링크")
for keyword in words:
            # 키워드가 악성 키워드에 포함된다면
            if keyword in gambler_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--도박")
            elif keyword in webtoon_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--웹툰")
            elif keyword in obscence_keywords:
                print(f"URL: {url} contains malicious keyword: {keyword}" + "--성인물")
print("----------------------------------------------------------------------------------------------")
# 오류가 발생한 URL 출력
print("\nFailed URLs:")
for url in failed_urls:
    print(url)

# 출력값/ 최종출력값:
# URL: https://linkall1.online/bbs/board.php?bo_table=adult contains malicious keyword: 성인--성인물
# 정상
# 정상
# URL: https://linkall1.online/bbs/board.php?bo_table=drama contains malicious keyword: 드라마--웹툰
# 정상
# 정상
# 정상
# URL: https://linkall1.online/bbs/board.php?bo_table=sports contains malicious keyword: 스포츠중계--도박
# 정상
# URL: https://linkall1.online/bbs/board.php?bo_table=torrent contains malicious keyword: 토렌트--도박
# 정상
# 정상
# URL: https://linkall1.online/bbs/board.php?bo_table=webtoon contains malicious keyword: 웹툰--웹툰
# 정상
# Error fetching https://linkall1.online/bbs/link.php?bo_table=torrent&wr_id=36&no=1: ('Connection aborted.', ConnectionResetError(10054, '현재 연결은 원격 호스트에 의해 강
# 제로 끊겼습니다', None, 10054, None))
# Failed URLs:
# https://publang.korean.go.kr/report/reportList.do
# https://cyberbureau.police.go.kr
# https://linkall1.online/bbs/link.php?bo_table=adult&wr_id=185&no=1
# https://linkall1.online/bbs/link.php?bo_table=adult&wr_id=125&no=1
# https://linkall1.online/bbs/link.php?bo_table=adult&wr_id=123&no=1
# https://linkall1.online/bbs/link.php?bo_table=adult&wr_id=126&no=1

# 모니터링 된 악성 링크
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 성인--성인물
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 드라마--웹툰
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 스포츠중계--도박
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 토렌트--도박
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 웹툰--웹툰
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 성인--성인물
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 드라마--웹툰
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 스포츠중계--도박
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 토렌트--도박
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 웹툰--웹툰
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 성인--성인물
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 드라마--웹툰
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 스포츠중계--도박
# URL: https://linkall1.online/index.php?device=mobile contains malicious keyword: 토렌트--도박