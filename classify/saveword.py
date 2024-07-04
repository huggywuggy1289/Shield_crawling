import logging
from classify.models import WordCount, FullSentence, Hosts, Normal, Casino, Adult, Copyright, Etc
from konlpy.tag import Okt
from collections import Counter
from asgiref.sync import sync_to_async
import random
import jpype
import re

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 형태소 분석기 객체 생성
okt = Okt()

def is_korean_or_english(word):
    # 한글 또는 영어가 포함된 단어만 필터링
    return bool(re.search('[가-힣a-zA-Z]', word))

def extract_korean_and_english_words(sentence):
    words = []
    # Okt 형태소 분석을 통해 명사와 다른 품사도 추출
    okt_pos = okt.pos(sentence)
    for word, pos in okt_pos:
        if pos in ['Noun', 'Verb', 'Adjective', 'Alpha']:  # 명사, 동사, 형용사, 영어 단어 추출
            words.append(word)
    return words

# FullSentence 테이블의 문장을 분석하고 WordCount 테이블에 저장하는 함수
async def analyze_and_store_full_sentence(host):
    logger.debug(f"Analyzing and storing full sentences for host: {host}")
    full_sentences = await sync_to_async(list)(
        FullSentence.objects.filter(host=host).values_list('full_sentence', flat=True))

    word_count = Counter()
    for sentence in full_sentences:
        words = extract_korean_and_english_words(sentence)
        filtered_words = [word for word in words if is_korean_or_english(word)]  # 한국어 또는 영어 단어만 필터링
        word_count.update(filtered_words)

    for word, count in word_count.items():
        await sync_to_async(WordCount.objects.create)(
            host=host,
            words=word,
            count=count
        )
    logger.debug("Finished analyzing and storing full sentences")

# 단어를 카테고리별 테이블에 저장하는 함수
async def save_keywords_to_category_tables():
    logger.debug("Saving keywords to category tables")

    categories = {
        "정상": Normal,
        "도박사이트": Casino,
        "성인사이트": Adult,
        "불법저작물배포사이트": Copyright,
        "기타": Etc,
    }

    for category, model in categories.items():
        # 기존 단어 삭제
        await sync_to_async(model.objects.all().delete)()

        # final 필드가 해당 카테고리인 경우의 단어 가져오기
        words_from_final = await sync_to_async(list)(
            WordCount.objects.filter(host__final=category).values_list('words', flat=True)
        )

        # final 필드가 비어 있고 classification 필드가 해당 카테고리인 경우의 단어 가져오기
        words_from_classification = await sync_to_async(list)(
            WordCount.objects.filter(host__final__isnull=True, host__classification=category).values_list('words', flat=True)
        )

        # 두 리스트 합치기
        words = words_from_final + words_from_classification

        if words:
            most_common_words = [word for word, _ in Counter(words).most_common(230)]  # 가장 많은 단어 230개 가져오기
            remaining_words = list(set(words) - set(most_common_words))
            random_words = random.sample(remaining_words, min(70, len(remaining_words)))  # 70개 랜덤으로 가져오기
            combined_words = most_common_words + random_words

            for word in combined_words:
                await sync_to_async(model.objects.create)(word=word)

    logger.debug("Finished saving keywords to category tables")

