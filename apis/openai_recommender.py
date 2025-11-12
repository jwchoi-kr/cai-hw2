import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from domain.models import DestinationCandidate, DestinationCandidates

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
)
prompt_template = """
너는 여행 계획 보조 AI야.
입력으로 여행지 후보들의 정보가 주어진다.
각 후보는 다음 구조를 가진 튜플이다:
(여행지 이름, 왕복 예상 소요 시간(시간 단위), 날씨 상태, 기온(°C), 대기질 상태)

예시:
("남이섬", 4.0, "GOOD", 12.3, "BAD")

주어진 여행지 후보 목록을 사용자의 선호 조건(must_include, likes),
여행 소요 시간(round_trip_hours), 그리고 날씨 요약(weather_summary: 날씨 상태, 기온, 대기질)을 함께 고려하여
상위 추천 여행지 {k}개를 골라줘.

규칙:
1) must_include
- 이름에서 must_include 목록과 명확히 관련 있으면 반드시 포함해.
- 연관성이 조금이라도 있어 보이면 웬만하면 포함해.

2) likes
- 사용자가 좋아하는 활동/분위기/장소 유형과 이름이 잘 어울리면 포함 우선순위를 높여.
- likes와 전혀 관련 없어 보이는 후보는 빼도 되지만, 너무 과하게 제거하지는 마.

3) round_trip_hours
- 소요 시간이 너무 길면 하루 일정에 부담이 될 수 있으므로, 일반적으로 5~6시간 이내의 후보를 우선 고려해.
- 단, 사용자의 선호와 매우 잘 맞는 장소라면 약간 더 긴 거리라도 포함해도 좋다.

4) weather_summary (날씨 상태, 기온, 대기질)
- 날씨 상태(weather_condition)가 맑음/화창함이면 실외 활동형 장소를 우선 추천해.
- 흐림/비/눈 등의 조건이면 실내 활동이나 짧은 일정에 적합한 장소를 추천해.
- 기온이 너무 낮거나 높을 경우, 야외 체류 시간이 긴 장소는 피하는 게 좋다.
- 대기질이 '나쁨' 이상이면 실내 중심 코스를 고려해.

5) 결과 선택
- 전체 후보 중에서 must_include, likes, 소요 시간, 날씨 정보를 종합적으로 고려해 상위 {k}개를 남겨.
- 추천 결과는 선호 적합도가 높은 순으로 정렬해.
- 각 여행지마다 선택 이유(reason)를 반드시 자세히 작성해(가능하면 3문장 이상).
- 선택 이유에는 사용자 선호를 명시적으로 인용해라. 예)
  "사용자가 '자연'을 선호한다고 했기 때문에 …",
  "must_include에 '미술관'이 있어 …",
  "날씨가 맑고 기온이 15도로 쾌적하여 야외활동에 적합함" 처럼 입력 정보를 그대로 언급해라.
- 가능하면 다른 후보 대비 비교 우위(거리, 날씨 적합성, 활동 종류 등)도 덧붙여라.

출력 형식:
- 반드시 다음 JSON 배열만 반환해(객체로 감싸지 마라).
  [
    {"place": "남이섬", "reason": "사용자가 '자연'을 선호한다고 했기 때문에 숲과 강 경관을 함께 즐길 수 있는 곳을 추천함. 맑은 날씨와 12도의 쾌적한 기온이 야외 산책에 적합함. 수도권에서 왕복 약 4시간으로 접근성도 좋아 하루 일정에 이상적임."},
    {"place": "양평 두물머리", "reason": "must_include에 '호수/강변'이 있어 강가의 풍경을 즐길 수 있는 이 장소를 포함함. 대기질이 '좋음'으로 쾌적해 산책이나 사진 촬영에 적합함. 거리도 3시간 이내라 이동이 편리함."}
  ]
- JSON 배열 외의 추가 문장이나 설명은 절대 쓰지 마.
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
            c.round_trip_hours,
            c.weather_summary.weather_condition.name,
            c.weather_summary.temperature,
            c.weather_summary.air_quality.name,
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
        text_format=DestinationCandidates,
        temperature=0,
    )

    return response.output_parsed.candidates
