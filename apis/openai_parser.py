import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import ParsedUserInput

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

prompt_template = """
너는 여행 계획 보조 AI야. 사용자의 문장을 분석해 여행 의도를 구조화된 데이터로 변환해야 해.
출력은 아래 스키마에 따라야 한다:

- origin (str): 출발지. 명시되어 있지 않으면 "미상".

- departure_time (str): 출발 시각.
    - 사용자가 "오늘 오후 3시", "내일 오전 10시", "10월 3일 3시" 등 자연어로 말하더라도,
      반드시 ISO 8601 형식 "YYYY-MM-DDTHH:MM:SS" 문자열로 변환해서 넣어라.
    - "오늘", "내일", "모레", "이번 토요일" 같은 표현은 기준 시각 {now_iso} 를 기준으로 해석해라.
    - 연도가 생략된 "10월 3일" 같은 표현은 기준 연도 {now.year} 를 사용해라.
    - 시/분이 일부만 주어졌다면, 분은 00으로 가정해도 된다.
    - 출발 시각이 전혀 언급되지 않으면 "미정"으로 넣어라.

- destination_categories (list[str]): 희망 장소 카테고리.
    - 아래 값 중 하나 이상을 포함해야 한다:
        - "TOURIST_SPOT"       : 관광명소 (자연, 경치, 산, 강, 섬, 바다, 유적지, 유명 관광지 등)
        - "CULTURE_FACILITY"   : 문화시설 (미술관, 박물관, 전시장, 공연장, 도서관, 과학관 등)

    - 분류 기준:
        1. 사용자가 "풍경", "자연", "호수", "산", "해변", "경치", "드라이브", "휴양" 등의 단어를 언급하면  
           → ["TOURIST_SPOT"]
        2. 사용자가 "미술관", "박물관", "공연", "전시", "영화관", "도서관", "전시회", "예술" 등의 단어를 언급하면  
           → ["CULTURE_FACILITY"]
        3. 두 유형의 단어가 모두 등장하거나,  
           "둘 다", "다양하게", "관광지도 좋고 미술관도 좋아요", "여행 중간에 전시회도 가고 싶어요" 같은 표현이면  
           → ["TOURIST_SPOT", "CULTURE_FACILITY"]
        4. 사용자가 구체적으로 언급하지 않은 경우  
           → ["TOURIST_SPOT"]

- max_travel_hours (float): 왕복 기준 최대 여행 가능 시간(시간 단위). 없으면 12로.
- budget (int | None): 예산(원 단위). 없으면 None.
- transportation (str | None): 교통수단(예: "자동차", "대중교통", "기차" 등). 없으면 None.
- companions (list[str] | None): 동행자 유형(예: "친구", "가족", "혼자" 등). 없으면 None.
- likes (list[str] | None): 선호 요소(예: "자연", "조용한 곳", "맛집" 등).
- dislikes (list[str] | None): 비선호 요소(예: "혼잡함", "실내" 등).
- must_include (list[str] | None): 반드시 포함해야 하는 장소나 활동.
- must_avoid (list[str] | None): 반드시 피해야 하는 요소.

- keyword (str | None): 장소 검색에 직접 사용할 키워드.
    - 사용자가 특정 장소 유형을 아주 명확하게 언급한 경우에만 설정한다.
    - 예시:
        * "미술관 추천해줘" → "미술관"
        * "양평 쪽 카페 말고, 서울에서 전시회 하는 곳" → "전시회"
        * "한적한 호수 근처로 가고 싶어" → "호수"
    - 단순한 분위기나 특징(예: "조용한 곳", "자연 풍경")만 말한 경우에는 None으로 둔다.
    - 애매하거나 중의적인 경우에는 **절대 채우지 말고 None으로 둔다.**

주의:
- 반드시 위 스키마에 맞는 JSON 구조만 생성해야 한다.
- departure_time은 "미정" 또는 "YYYY-MM-DDTHH:MM:SS" 형식의 문자열 중 하나여야 한다.

아래 사용자의 입력을 분석해 위 형식으로 반환하라:
"{user_input}"
"""


def parse_user_input(user_input: str) -> ParsedUserInput:
    now = datetime.now()
    now_iso = now.isoformat()

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": prompt_template.format(
                    now_iso=now_iso, now=now, user_input=user_input
                ).strip(),
            },
        ],
        text_format=ParsedUserInput,
        temperature=0,
    )

    return response.output_parsed
