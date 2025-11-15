import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import FilteredPlaces, ParsedUserInfo, PlaceInfo

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

MULTIPLIER = 6

prompt_template = """
너는 여행 계획 보조 AI야.
주어진 여행지 후보 목록을 사용자의 비선호 조건에 따라 '필터링'만 해서 돌려줘.

규칙:
1) must_avoid
- 이름에 must_avoid 목록의 단어가 그대로 포함되거나,
  매우 직접적으로 연상되는 경우에만 제외해라.
- 애매하거나 간접적인 연관 정도라면 제거하지 말고 남겨둬도 된다.
- must_avoid는 여행자가 정말 피하고 싶은 경우이기 때문에,
  "확실한 경우에만" 적용해라.

2) dislikes
- dislikes와 관련 있어 보이는 이름은 가능하면 제외하되,
  이건 어디까지나 "선호도 반영"일 뿐 필수 조건은 아니다.
- 후보 개수가 이미 {k_min}개에 가깝거나 그보다 적다면,
  dislikes에 걸리더라도 웬만하면 남겨둬도 괜찮다.
- 후보가 너무 많을 때(예: {k_max}개를 초과할 때) 정리할 때
  dislikes에 더 많이 걸리는 장소를 우선적으로 제거하는 용도로 사용해라.
- must_avoid보다 우선순위가 낮다.

3) 결과 개수 규칙
- 최종 결과 리스트 길이는 가능하면 {k_min}개 이상, {k_max}개 이하가 되도록 해라.
- 필터링 결과가 {k_min}개보다 적더라도 절대 새로운 장소를 만들거나 추가하지 마라.
- must_avoid를 적용한 뒤 남은 후보가 {k_min}개 미만이라면,
  추가로 더 제거하지 말고 그대로 두어라.
- 후보가 {k_max}개보다 많이 남으면,
  dislikes에 더 많이 걸리거나, 덜 특징적인 장소부터 제거해서
  {k_max}개에 가까워지도록 줄여라.
- 이 방법으로도 {k_max}개보다 많다면,
  **남은 후보들 중 임의로(random) 골라서 {k_max}개가 되도록 제거해라.**
"""


def filter_candidates_by_user_preferences(
    candidates: List[PlaceInfo],
    user_preferences: ParsedUserInfo,
    candidate_size: int,
) -> List[PlaceInfo]:
    if not candidates or candidate_size <= 0:
        return []

    # 결과 최소/최대 개수
    k_min = candidate_size
    k_max = candidate_size * MULTIPLIER

    # 후보지 이름 리스트
    candidates_names = [c.place_name for c in candidates]

    # 프롬프트에 k_min/k_max 적용
    formatted_prompt = prompt_template.format(k_min=k_min, k_max=k_max).strip()

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
        temperature=0.5,
    )

    filtered_names = response.output_parsed.places

    # 원본 PlaceInfo 객체로 매칭
    filtered_candidates = [c for c in candidates if c.place_name in filtered_names]

    return filtered_candidates[:k_max]
