import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import ParsedUserInfo

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

prompt_template = """
너는 여행 계획 보조 AI이며, 사용자가 제공한 입력을 기반으로
여행 조건을 구조화된 JSON 형태로 반환하는 역할을 한다.

반환 스키마:
- origin (str): 출발지. 언급 없으면 "미상".
- departure_datetime (str)
    - 사용자 표현을 → ISO 8601 "YYYY-MM-DDTHH:MM:SS"
    - “오늘/내일/모레/이번 토요일/다음 주말” 등 상대적 표현은 now_iso 기준
    - 시간 미언급이면 "미정" 또는 now_iso 중 하나 선택 가능
- destination_categories (list[str])
    규칙:
      * 자연/풍경/호수/산/드라이브 → ["TOURIST_SPOT"]
      * 미술관/전시/박물관/영화관 → ["CULTURE_FACILITY"]
      * 둘 다 언급 → ["TOURIST_SPOT", "CULTURE_FACILITY"]
      * 아무 것도 없으면 기본값 ["TOURIST_SPOT"]

- max_travel_hours (float): 언급 없으면 12.

- transportation (str | None):
    - 자동차, 차 → "CAR"
    - 버스, 지하철, 대중교통 → "PUBLIC"
    - 없으면 None.

- likes (list[str] | None)
- dislikes (list[str] | None)
- must_include (list[str] | None)
- must_avoid (list[str] | None)

- keyword (str | None):
    * 장소 유형이 명확하게 언급될 때만 설정
    * 분위기/추상 표현만 있을 경우 None

아래 입력을 ParsedUserInfo JSON으로 변환해라:

사용자 입력:
"{user_input}"

현재 시각 (ISO):
{now_iso}
"""


def parse_user_info(user_input: str) -> ParsedUserInfo:
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
        text_format=ParsedUserInfo,
        temperature=0,
    )

    return response.output_parsed
