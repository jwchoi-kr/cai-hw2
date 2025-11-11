import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import DestinationCandidate, FinalCandidate, FinalCandidates

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

prompt_template = """
너는 여행 계획 보조 AI야.
주어진 여행지 후보 목록을 사용자의 선호 조건(must_include, likes)에 따라 상위 추천 여행지들을 골라줘.

규칙:
1) must_include
- 이름에서 must_include 목록과 명확히 관련 있으면 반드시 포함해.
- 연관성이 조금이라도 있어 보이면 웬만하면 포함해.

2) likes
- 사용자가 좋아하는 활동/분위기/장소 유형과 이름이 잘 어울리면 포함 우선순위를 높여.
- likes와 전혀 관련 없어 보이는 후보는 빼도 되지만, 너무 과하게 제거하지는 마.

3) 결과 선택
- 전체 후보 중에서 사용자의 취향에 잘 맞는 상위 여행지들을 남겨.
- 각 여행지마다 선택 이유를 반드시 자세히 작성해.
- reason은 must_include / likes와의 연관성, 분위기, 활동, 비교 우위 등을 구체적으로 설명해.
- 가능한 한 3문장 이상으로 자세히 써도 된다.

출력 형식:
- 반드시 다음 JSON 형식으로 답변해.
  [
    {"place": "남이섬", "reason": "자연 경관이 아름답고 커플 여행지로 유명함..."},
    {"place": "양평 두물머리", "reason": "강변 산책로와 조용한 분위기로 데이트에 적합함..."}
  ]
- JSON 배열만 반환하고, 추가 문장이나 설명은 절대 쓰지 마.
"""


def recommend_top_k_candidates(
    candidates: List[DestinationCandidate],
    must_include: List[str],
    likes: List[str],
    k: int,
) -> List[FinalCandidate]:
    if not candidates or k <= 0:
        return []

    candidates_names = [c.place_info.place_name for c in candidates]

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
                        "candidates": candidates_names,
                        "top_k": k,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        text_format=FinalCandidates,
        temperature=0,
    )

    final_list: List[FinalCandidate] = response.output_parsed.candidates

    return final_list[:k]
