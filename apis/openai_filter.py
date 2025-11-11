import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import FilteredPlaces, ParsedUserInput, PlaceInfo

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

prompt_template = """
너는 여행 계획 보조 AI야.
주어진 여행지 후보 목록을 사용자의 비선호 조건에 따라 '필터링'만 해서 돌려줘.

규칙:
1) must_avoid
- 이름에 must_avoid 목록과 명확히 관련 있거나, 조금이라도 연관된 여행지는 모두 제거해.
- 애매하면 남기지 말고 안전하게 제거해.

2) dislikes
- dislikes와 관련 있거나 연상되는 이름은 가능하면 제외하되, 너무 빡세게 걸러내지는 마.
- 애매한 경우에는 제거하지 말고 남겨둬도 된다.
- must_avoid보다 우선순위가 낮다. (must_avoid는 무조건 제외, dislikes는 "가급적" 제외)

3) 결과
- 최종적으로 불필요하거나 비선호 여행지는 최대한 제거하되,
  전체 후보 중 약 {k}개 내외(±2개 정도)의 여행지만 남기도록 해라.
- 만약 규칙을 너무 엄격하게 적용해서 {k}개보다 훨씬 적게 남는다면,
  dislikes 기준을 다소 완화해서라도 {k}개에 가깝게 맞춰라.
- 반대로 너무 많이 남는다면, 상대적으로 비선호에 가깝거나 일반적인 장소들을 우선적으로 제외해라.
- 결국 결과는 약 {k}개 전후의 “적당한 개수”가 되어야 한다.
"""


def filter_candidates_by_user_preferences(
    candidates: List[PlaceInfo],
    user_preferences: ParsedUserInput,
    candidate_size: int,
) -> List[PlaceInfo]:
    if not candidates or candidate_size <= 0:
        return []

    # 후보지 이름만 추출
    candidates_names = [c.place_name for c in candidates]

    # 프롬프트에 k(candidate_size) 주입
    formatted_prompt = prompt_template.format(k=candidate_size).strip()

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": formatted_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "preferences": {
                            "dislikes": user_preferences.dislikes or [],
                            "must_avoid": user_preferences.must_avoid or [],
                        },
                        "candidates": candidates_names,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        text_format=FilteredPlaces,
        temperature=0,
    )

    filtered_names = response.output_parsed.places

    # 원래 PlaceInfo 리스트에서 이름으로 매칭
    filtered_candidates = [c for c in candidates if c.place_name in filtered_names]

    return filtered_candidates
