import json
from typing import List

from domain.models import DestinationCandidate
from apis.openai_parser import client
from apis.kakao_local import (
    get_coords_by_address,
    get_travel_candidates_by_distance,
)


def generate_recommendation(
    user_input: str, destination_candidates: list[DestinationCandidate],
    radius_restaurant: int = 5000
) -> tuple[str, str]:
    
    # 프롬프트 생성
    candidates_text = ""
    for i, candidate in enumerate(destination_candidates):
        candidates_text += \
            f"여행지 {i+1}. {candidate.place_info.place_name}: " \
            f"{candidate.round_trip_hours}시간 왕복 거리, " \
            f"현재 날씨는 {candidate.weather.current.weather_condition.name}" \
            f"({candidate.weather.current.temperature}°C, " \
            f"공기질, {candidate.weather.current.air_quality.name}), " \
            f"요청에 적합한 이유와 특징: {', '.join(candidate.reasons)} \n"

    prompt = f"""
    당신은 유용한 여행 추천 전문가입니다.
    [사용자 요청]을 바탕으로 아래 [여행지 후보] 중 가장 적절한 여행지 한 곳을 선택하세요.
    description에는 해당 여행지를 선택한 구체적인 이유를 포함하여, 
    해당 여행지를 사용자에게 추천하는 문구를 작성하세요.
    예를 들어, 사용자의 요청을 고려했을 때 왜 적합한지 구체적으로 설명하면서,
    날씨, 이동 시간, 특징 등을 적절하게 언급할 수 있습니다.
    따뜻하고 친근한 말투로 여행지를 추천하고, 
    텍스트는 여행 블로그나 가이드북처럼 자연스럽고 부드럽게 표현되어야 합니다.

    [사용자 요청]
    {user_input}

    [여행지 후보]
    {candidates_text}

    출력 형식은 다음 JSON 형태로만 답변하세요:
    {{
        "index": "<선택한 여행지 번호>",
        "description": "<추천지와 추천 이유 (특히, 사용자의 요청과 어떻게 부합하는지)>"
    }}
    """
    # print(prompt)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    import json

    content = response.choices[0].message.content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return None, None
    # print(result)

    # 음식점 검색
    destination_final = destination_candidates[int(result["index"]) - 1]
    destination_final_name = destination_final.place_info.place_name
    lat, lon = get_coords_by_address(destination_final.place_info.address_name)
    restaurant = get_travel_candidates_by_distance(
        lat, lon, radius=radius_restaurant, category_group_code="FD6"
    )[0]

    # 최종 텍스트 생성
    output = result["description"]
    if restaurant:
        output += f" 식사는 근처 {restaurant.distance_m}m 거리에 있는 맛집, " + \
        f"{restaurant.place_name} 어떠세요?"

    return output, destination_final_name
