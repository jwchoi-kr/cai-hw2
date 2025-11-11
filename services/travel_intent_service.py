from typing import List

from apis.kakao_local_address import get_coords
from apis.kakao_local_candidates import (
    get_travel_candidates,
)
from apis.kakao_local_trip_hours import get_round_trip_hours
from apis.openai_filter import filter_candidates_by_user_preferences
from apis.openai_parser import parse_user_input
from apis.openai_scorer import recommend_top_k_candidates
from apis.weather import get_weather_summary
from domain.models import DestinationCandidate, PlaceInfo
from utils.distance_helper import time_to_radius_m


def generate_travel_candidates(user_input: str, k: int) -> List[DestinationCandidate]:
    # 1. 유저의 input으로부터 여행 정보 파싱
    parsed_user_input = parse_user_input(user_input)
    print("1. Parsed user input:", parsed_user_input)

    # 2. 출발지 주소 -> 좌표 변환
    origin_lat, origin_lon = get_coords(parsed_user_input.origin)
    print(f"2. Origin coords: lat={origin_lat}, lon={origin_lon}")

    # 3. 이동 가능 거리 나이브하게 계산
    radius_m = time_to_radius_m(
        parsed_user_input.max_travel_hours, parsed_user_input.transportation
    )
    print(f"3. Calculated radius (km): {radius_m / 1000}")

    # 4. 반경 내 여행지 후보지 검색
    candidates: List[PlaceInfo] = get_travel_candidates(
        origin_lat, origin_lon, radius_m, parsed_user_input.destination_categories
    )
    print(f"4. {len(candidates)} candidates after distance-based retrieval")

    # 5. 유저의 비선호 조건에 따른 필터링
    filtered_by_preference_candidates: List[PlaceInfo] = (
        filter_candidates_by_user_preferences(candidates, parsed_user_input, 3 * k)
    )
    print(
        f"5. {len(filtered_by_preference_candidates)} candidates after filtering by preferences"
    )

    # 6. 각 여행지 별로 실제 소요 시간 계산
    filtered_by_distance_candidates: List[DestinationCandidate] = []
    for candidate in filtered_by_preference_candidates:
        round_trip_hours = get_round_trip_hours(
            parsed_user_input.departure_time,
            origin_lat,
            origin_lon,
            candidate.dest_lat,
            candidate.dest_lon,
        )

        # 6. 충분하게 여행을 다녀올 수 없는 후보지는 제외
        if round_trip_hours / 2 > parsed_user_input.max_travel_hours:
            continue

        # # 7. 날씨 정보 가져오기
        # weather_summary = get_weather_summary(
        #     lat=candidate.dest_lat,
        #     lon=candidate.dest_lon,
        #     input_iso=parsed_user_input.departure_time,
        #     duration_hours=round_trip_hours,
        # )

        destination_candidate = DestinationCandidate(
            place_info=candidate,
            round_trip_hours=round_trip_hours,
        )
        filtered_by_distance_candidates.append(destination_candidate)
    print(
        f"6. {len(filtered_by_distance_candidates)} candidates within travel time limit"
    )

    # 7. top k 후보지 선정
    top_k_candidates = recommend_top_k_candidates(
        filtered_by_distance_candidates,
        parsed_user_input.must_include or [],
        parsed_user_input.likes or [],
        k,
    )

    print(f"7. {len(top_k_candidates)} candidates after recommending top k")

    return top_k_candidates
