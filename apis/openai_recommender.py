import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import (
    DestinationCandidate,
    LLMRecommendedCandidates,
)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

prompt_template = """
너는 여행 계획 보조 AI야.
입력으로 여행지 후보들의 정보가 주어진다.
각 후보는 다음 구조의 튜플이다:

(여행지 이름, 실외 활동 적합도 점수)

예시:
("남이섬", 85)

여기서:
- 실외 활동 적합도 점수(outdoor_score)는 0~100 정수이며,
  숫자가 높을수록 야외 활동에 더 유리함을 의미한다.

사용자의 선호 조건(must_include, likes)와
실외 활동 적합도 점수(outdoor_score)를 함께 고려하여  
최적의 여행지 정확히 **{k}개**를 골라라.

-------------------------------------------------------
규칙:

1) must_include
- must_include 키워드와 의미상 잘 맞는 장소는 우선적으로 포함하라.
- 다만 outdoor_score가 매우 낮거나, 관련성이 약한 경우에는 포함하지 않아도 된다.

2) likes 적용
- "자연", "호수", "조용한 곳", "해변" 등 likes에 부합하면 가산점.
- likes와 무관하면 가산점 없음, 반대 성격이면 감점.

3) 날씨 규칙
- outdoor_score가 높은 후보일수록 순위가 올라야 한다.
    최종 점수 해석:
        • 80~100 → 실외 활동에 매우 적합
        • 60~79  → 무난하게 가능
        • 40~59  → 다소 애매함
        • 20~39  → 실외 비추천
        • 0~19   → 실외 활동 거의 불가능


4) 결과 개수 규칙 (매우 중요)
- 후보가 10개 이상이면 → **정확히 10개**만 반환.
- 후보가 10개 미만이면 → **있는 만큼만 반환 (새 창작 금지)**.
- 새로운 장소를 생성하거나 입력에 없는 이름을 만들어내면 안 된다.
- 동일한 장소를 중복 포함해서도 안 된다.

-------------------------------------------------------
출력 형식:
반드시 다음 JSON 객체 하나만 반환해.

{
  "candidates": [
    {
      "place_name": "남이섬",
      "reason": "사용자가 자연스럽고 조용한 장소를 선호한다고 하여 분위기와 잘 맞습니다. 오늘은 맑고 야외에서 걷기 좋은 날씨라 풍경을 즐기기에 적합해 추천합니다."
    },
    {
      "place_name": "양평 두물머리",
      "reason": "호수·강변 풍경을 좋아하는 조건과 잘 맞는 장소입니다. 비도 거의 없고 날씨도 안정적이라 산책하거나 사진 찍기 좋은 환경이라 추천드립니다."
    }
  ]
}

- JSON 외 다른 문장/설명은 절대 쓰지 마..
"""


def recommend_top_k_candidates(
    candidates: List[DestinationCandidate],
    must_include: List[str],
    likes: List[str],
    k: int,
) -> List[DestinationCandidate]:
    if not candidates or k <= 0:
        return []

    candidates_summary = [
        (
            c.place_info.place_name,
            c.outdoor_score,
        )
        for c in candidates
    ]

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": prompt_template.strip()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "preferences": {
                            "must_include": must_include,
                            "likes": likes,
                        },
                        "candidates": candidates_summary,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        text_format=LLMRecommendedCandidates,
        temperature=0,
    )

    llm_result: LLMRecommendedCandidates = response.output_parsed

    # place_name → DestinationCandidate 매핑
    name_to_candidate: dict[str, DestinationCandidate] = {
        c.place_info.place_name: c for c in candidates
    }

    ordered: List[DestinationCandidate] = []
    for rec in llm_result.candidates:
        cand = name_to_candidate.get(rec.place_name)
        if cand is None:
            # LLM이 이상한 이름을 뱉으면 그냥 무시
            continue
        # reason 채워넣기
        cand.reason = rec.reason
        ordered.append(cand)

    # 혹시 LLM이 k개보다 많이 줬으면 k개까지만 자르기
    return ordered[:k]
