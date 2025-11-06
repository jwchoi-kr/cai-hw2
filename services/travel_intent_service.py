import json
from typing import List

from apis.kakao_local import (
    get_coords,
    get_travel_candidates_by_distance,
)
from apis.openai_parser import parse_travel_intent
from domain.models import PlaceInfo
from utils.distance_helper import time_to_radius


def generate_travel_candidates(user_input: str) -> List[PlaceInfo]:
    # 여행 의도 파싱
    parsed_intent = parse_travel_intent(user_input)
    print(json.dumps(parsed_intent.model_dump(), indent=2, ensure_ascii=False))

    # 주소 -> 좌표 변환
    lat, lon = get_coords(parsed_intent.origin)
    print(f"Origin coords: lat={lat}, lon={lon}")

    # 이동 가능 거리 계산 후 여행지 가져옴
    radius = time_to_radius(
        parsed_intent.travel_duration_hours, parsed_intent.transportation
    )
    print(f"Calculated search radius (km): {radius}")
    print(f"Search radius (m): {radius}")
    candidates = get_travel_candidates_by_distance(lat, lon, radius)

    return candidates
