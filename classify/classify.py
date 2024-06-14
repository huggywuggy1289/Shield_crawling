import openai
from classify.models import WordCount

# OPENAI_API_KEY 설정
OPENAI_API_KEY = ""
openai.api_key = OPENAI_API_KEY

def get_top10_keywords(host):
    return (WordCount.objects
            .filter(host=host)
            .order_by('-count')
            .values_list('words', flat=True)[:10])

def classify_site(top_10_keywords):
    if not top_10_keywords:
        return "접속 불가 또는 존재하지않음"

    keywords_sentence = ", ".join(top_10_keywords)
    question = f"웹사이트의 top 10 키워드입니다: {keywords_sentence}. 웹사이트가 다음 중 어떤 종류인지 판단해주세요: 도박사이트, 성인사이트, 무료웹툰사이트, 토렌트, 정상. 부연설명은 필요없어."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    classification = response.choices[0].message['content'].strip()

    if any(word in classification for word in ["도박사이트", "성인사이트", "무료웹툰사이트", "토렌트", "정상"]):
        return classification
    else:
        return "알 수 없음"

def update_classification_in_db(host, classification):
    WordCount.objects.filter(host=host).update(classification=classification)
