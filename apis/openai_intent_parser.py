import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from domain.enums import ChatIntent
from domain.models import ParsedUserIntent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

prompt_template = """
너는 한국어 여행 챗봇의 '발화 의도 분류기' 역할을 한다.
사용자 발화를 보고 네 가지 intent(TRIP_INFO, NEXT_CANDIDATE, FOLLOW_UP, UNKNOWN) 중
딱 하나만 고른다.

가능한 intent:
- TRIP_INFO:
    새로운 여행 조건을 말하거나 기존 조건을 보완하는 경우.
- NEXT_CANDIDATE:
    이미 여행지 추천을 받은 상태에서 '다른 후보 자체'를 요청하는 경우.
- FOLLOW_UP:
    방금 추천된 장소를 전제로 상세 질문, 조건 변경, 비교를 요청하는 경우.
- UNKNOWN:
    위 세 가지로 분류할 수 없거나 금지 콘텐츠 포함.

[has_already_recommended 활용 규칙]
- has_already_recommended = False:
      NEXT_CANDIDATE, FOLLOW_UP 으로 절대 분류하지 않는다.
      여행 조건 관련 내용이면 TRIP_INFO, 그 외는 UNKNOWN.

- has_already_recommended = True:
      "다른 곳", "또 추천해줘", "다음 후보" → NEXT_CANDIDATE  
      추천된 장소 기반 질문/조건 변경 → FOLLOW_UP  
      완전히 새로운 여행 조건 → TRIP_INFO
      위 세 가지에 해당하지 않으면 UNKNOWN.

[안전/윤리 규칙]
다음 내용은 무조건 UNKNOWN:
- 자해/극단적 선택
- 폭력/범죄/불법행위/스토킹/사생활 침해
- 미성년자 관련 부적절한 성적 내용
- 혐오 발언
- 사기/금전 피해 유도
- 불법‧위험 활동 장소 추천 요청

intent 하나만 반환해라.
"""


def parse_user_intent(
    user_text: str,
    has_already_recommended: bool,
) -> ChatIntent:
    """
    LLM을 사용해서 사용자의 발화를 ChatIntent 중 하나로 분류한다.
    Args:
        user_text: 사용자가 입력한 텍스트
        has_already_recommended: 이미 여행지 후보를 하나 이상 추천한 뒤의 대화인지 여부
    """

    payload = {
        "has_already_recommended": has_already_recommended,
        "utterance": user_text,
    }

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": prompt_template.strip()},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
        text_format=ParsedUserIntent,
        temperature=0,
    )

    parsed = response.output_parsed
    return parsed.intent
