import openai
import logging
from classify.models import WordCount, FullSentence, Hosts, Normal, Casino, Adult, Copyright
from konlpy.tag import Okt
from collections import Counter
from asgiref.sync import sync_to_async

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# OPENAI_API_KEY 설정
OPENAI_API_KEY = ""  # 여기에 실제 API 키를 입력하세요.
openai.api_key = OPENAI_API_KEY

# 형태소 분석기 객체 생성
okt = Okt()

# 상위 10개의 키워드를 가져오는 함수
async def get_top10_keywords(host):
    logger.debug(f"Fetching top 10 keywords for host: {host}")
    return await sync_to_async(list)(WordCount.objects
                                     .filter(host=host)
                                     .order_by('-count')
                                     .values_list('words', flat=True)[:10])

# 미리 정의된 키워드를 가져오는 함수
async def get_predefined_keywords():
    logger.debug("Fetching predefined keywords from database")
    predefined_keywords = {
        "도박사이트": await sync_to_async(list)(Casino.objects.values_list('word', flat=True)),
        "성인사이트": await sync_to_async(list)(Adult.objects.values_list('word', flat=True)),
        "불법저작물배포사이트": await sync_to_async(list)(Copyright.objects.values_list('word', flat=True)),
        "정상": await sync_to_async(list)(Normal.objects.values_list('word', flat=True)),
    }
    return predefined_keywords

# 숫자로 응답받기 위한 함수
async def classify_with_keywords(question):
    response = await sync_to_async(openai.ChatCompletion.create)(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    classification = response.choices[0].message['content'].strip()
    logger.debug(f"Received classification: {classification}")
    return classification

# 상위 10개의 키워드를 사용하여 사이트 분류
async def classify_site(top_10_keywords):
    logger.debug(f"Classifying site using top 10 keywords: {top_10_keywords}")
    if not top_10_keywords:
        logger.warning("No keywords found, returning '접속 불가 또는 존재하지않음'")
        return "접속 불가 또는 존재하지않음"

    predefined_keywords = await get_predefined_keywords()
    predefined_keywords_sentence = {
        category: ", ".join(keywords)
        for category, keywords in predefined_keywords.items()
    }
    keywords_sentence = ", ".join(top_10_keywords)
    question = (f"웹사이트의 top 10 키워드입니다: {keywords_sentence}. "
                f"미리 정의된 카테고리별 키워드는 다음과 같습니다. "
                f"도박사이트: {predefined_keywords_sentence['도박사이트']}, "
                f"성인사이트: {predefined_keywords_sentence['성인사이트']}, "
                f"불법저작물배포사이트: {predefined_keywords_sentence['불법저작물배포사이트']}, "
                f"정상: {predefined_keywords_sentence['정상']}. "
                "위 미리 정의된 카테고리별 키워드를 참고하여 웹사이트가 다음 중 어떤 종류인지 숫자로 판단해줘: "
                "도박사이트(0), 성인사이트(1), 불법저작물배포사이트(2), 정상(3). "
                "부연설명은 필요없어. 도박사이트면 그냥 '0' 이런식으로만 출력해주면 돼")

    return await classify_with_keywords(question)

# 모든 키워드를 가져오는 함수
async def get_all_keywords(host):
    logger.debug(f"Fetching all keywords for host: {host}")
    words = await sync_to_async(list)(WordCount.objects
                                      .filter(host=host)
                                      .values_list('words', flat=True))
    return words

# 모든 키워드를 사용하여 사이트 분류
async def classify_all_keywords(host):
    logger.debug(f"Classifying site using all keywords for host: {host}")
    all_keywords = await get_all_keywords(host)
    if not all_keywords:
        logger.warning("No keywords found, returning '접속 불가 또는 존재하지않음'")
        return "접속 불가 또는 존재하지않음"

    predefined_keywords = await get_predefined_keywords()
    predefined_keywords_sentence = {
        category: ", ".join(keywords)
        for category, keywords in predefined_keywords.items()
    }
    keywords_sentence = ", ".join(all_keywords)
    question = (f"웹사이트의 모든 키워드입니다: {keywords_sentence}. "
                f"미리 정의된 카테고리별 키워드는 다음과 같습니다. "
                f"도박사이트: {predefined_keywords_sentence['도박사이트']}, "
                f"성인사이트: {predefined_keywords_sentence['성인사이트']}, "
                f"불법저작물배포사이트: {predefined_keywords_sentence['불법저작물배포사이트']}, "
                f"정상: {predefined_keywords_sentence['정상']}. "
                "위 미리 정의된 카테고리별 키워드를 참고하여 웹사이트가 다음 중 어떤 종류인지 숫자로 판단해줘: "
                "도박사이트(0), 성인사이트(1), 불법저작물배포사이트(2), 정상(3). "
                "부연설명은 필요없어. 도박사이트면 그냥 '0' 이런식으로만 출력해주면 돼")

    return await classify_with_keywords(question)

# FullSentence 테이블에서 문장을 요약하는 함수
async def summarize_full_sentence(host):
    logger.debug(f"Summarizing full sentences for host: {host}")
    full_sentences = await sync_to_async(list)(
        FullSentence.objects.filter(host=host).values_list('full_sentence', flat=True))

    combined_sentences = " ".join(full_sentences)
    question = f"다음 문장을 2-3문장으로 요약해줘: {combined_sentences}"

    response = await sync_to_async(openai.ChatCompletion.create)(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    summary = response.choices[0].message['content'].strip()
    logger.debug(f"Received summary: {summary}")
    return summary

# 요약문을 사용하여 사이트 분류
async def classify_summary(host):
    logger.debug(f"Classifying site using summary for host: {host}")
    summary = await summarize_full_sentence(host)
    predefined_keywords = await get_predefined_keywords()
    predefined_keywords_sentence = {
        category: ", ".join(keywords)
        for category, keywords in predefined_keywords.items()
    }
    question = (f"다음 요약문을 기반으로 웹사이트가 어떤 종류인지 숫자로 판단해줘: {summary}. "
                f"미리 정의된 카테고리별 키워드는 다음과 같습니다. "
                f"도박사이트: {predefined_keywords_sentence['도박사이트']}, "
                f"성인사이트: {predefined_keywords_sentence['성인사이트']}, "
                f"불법저작물배포사이트: {predefined_keywords_sentence['불법저작물배포사이트']}, "
                f"정상: {predefined_keywords_sentence['정상']}. "
                "위 미리 정의된 카테고리별 키워드를 참고하여 웹사이트가 다음 중 어떤 종류인지 숫자로 판단해줘: "
                "도박사이트(0), 성인사이트(1), 불법저작물배포사이트(2), 정상(3). "
                "부연설명은 필요없어. 도박사이트면 그냥 '0' 이런식으로만 출력해주면 돼")

    return await classify_with_keywords(question)

# 유사도를 확인하는 함수
async def check_similarity_with_predefined(host):
    logger.debug(f"Checking similarity for host: {host}")
    all_keywords = await get_all_keywords(host)
    predefined_keywords = await get_predefined_keywords()

    # 유사도 계산
    similarity_scores = {}
    for category, keywords in predefined_keywords.items():
        if not keywords:
            similarity_scores[category] = -1  # 키워드가 없으면 유사도 점수는 -1
            continue

        common_words = set(all_keywords) & set(keywords)
        similarity_scores[category] = len(common_words)

    logger.debug(f"Similarity scores: {similarity_scores}")
    most_similar_category = max(similarity_scores, key=similarity_scores.get)
    logger.debug(f"Most similar category: {most_similar_category}")

    # 유사도 점수가 모두 -1일 경우 처리
    if all(score == -1 for score in similarity_scores.values()):
        return -1

    return most_similar_category

# 최종 분류를 결정하는 함수
async def final_classification(host):
    logger.debug(f"Starting final classification for host: {host}")
    classifications = []

    # Top 10 단어 기반 분류
    top_10_keywords = await get_top10_keywords(host)
    top_10_classification = await classify_site(top_10_keywords)
    classifications.append(top_10_classification)
    logger.debug(f"Top 10 keywords classification: {top_10_classification}")

    # 모든 단어 기반 분류
    all_keywords_classification = await classify_all_keywords(host)
    classifications.append(all_keywords_classification)
    logger.debug(f"All keywords classification: {all_keywords_classification}")

    # 요약문 기반 분류
    summary_classification = await classify_summary(host)
    classifications.append(summary_classification)
    logger.debug(f"Summary classification: {summary_classification}")

    # 유사도 기반 분류
    similarity_classification = await check_similarity_with_predefined(host)
    classifications.append(similarity_classification)
    logger.debug(f"Similarity classification: {similarity_classification}")

    # 가장 많은 답변을 최종 분류로 결정
    filtered_classifications = [c for c in classifications if c != -1]  # -1을 제외한 분류 결과 사용
    if not filtered_classifications:
        final_classification_number = -1
    else:
        final_classification_number = Counter(filtered_classifications).most_common(1)[0][0]

    classification_map = {
        "0": "도박사이트",
        "1": "성인사이트",
        "2": "불법저작물배포사이트",
        "3": "정상",
        "-1": "알 수 없음"
    }
    final_classification = classification_map.get(final_classification_number, "알 수 없음")
    logger.debug(f"Final classification result: {final_classification}")
    return final_classification
