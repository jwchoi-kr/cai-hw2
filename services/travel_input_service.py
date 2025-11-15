from typing import List

from apis.kakao_local_address import get_coords
from apis.kakao_local_candidates import (
    get_travel_candidates,
)
from apis.openai_filter import filter_candidates_by_user_preferences
from apis.openai_info_parser import parse_user_info
from apis.openai_recommender import recommend_top_k_candidates
from apis.route import get_round_trip_hours
from apis.weather import get_weather_new
from domain.enums import Transportation
from domain.models import (
    ChatSessionState,
    DestinationCandidate,
    PlaceInfo,
)
from utils.distance_helper import max_travel_hours_to_radius_m
from utils.weather_helper import calculate_outdoor_score


def generate_travel_candidates(
    user_input: str, k: int, state: ChatSessionState
) -> List[DestinationCandidate]:
    # 1. 유저의 input으로부터 여행 정보 파싱
    parsed_user_info = parse_user_info(user_input)
    print("1. Parsed user input:", parsed_user_info)

    # 2. 출발지 주소 -> 좌표 변환
    origin_lat, origin_lon = get_coords(parsed_user_info.origin)
    print(f"2. Origin coords: lat={origin_lat}, lon={origin_lon}")

    # 3. 이동 가능 거리 나이브하게 계산
    radius_m = max_travel_hours_to_radius_m(
        parsed_user_info.max_travel_hours, parsed_user_info.transportation
    )
    print(f"3. Calculated radius (km): {radius_m / 1000}")

    # 4. 반경 내 여행지 후보지 검색
    candidates: List[PlaceInfo] = get_travel_candidates(
        origin_lat, origin_lon, radius_m, parsed_user_info.destination_categories
    )
    print(f"4. {len(candidates)} candidates after distance-based retrieval")

    # 5. 유저의 비선호 조건에 따른 필터링
    filtered_by_preference_candidates: List[PlaceInfo] = (
        filter_candidates_by_user_preferences(candidates, parsed_user_info, k)
    )
    print(
        f"5. {len(filtered_by_preference_candidates)} candidates after filtering by preferences"
    )

    # 6. 여행 시간 내에 다녀올 수 있는 후보지 선별 및 날씨 정보 추가
    enriched_candidates: List[DestinationCandidate] = []

    for candidate in filtered_by_preference_candidates:
        # 6-1. 왕복 여행 시간 계산
        round_trip_hours_dict = get_round_trip_hours(
            transportation=parsed_user_info.transportation,
            departure_datetime=parsed_user_info.departure_datetime,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=candidate.dest_lat,
            dest_lon=candidate.dest_lon,
        )

        # 6-2. 충분하게 여행을 다녀올 수 없는 후보지는 제외
        car_time = round_trip_hours_dict.get(Transportation.CAR)
        public_time = round_trip_hours_dict.get(Transportation.PUBLIC)

        if car_time is None:
            shortest_time = public_time
        elif public_time is None:
            shortest_time = car_time
        else:
            shortest_time = min(car_time, public_time)

        # 필터링
        if shortest_time > parsed_user_info.max_travel_hours * 0.5:
            continue

        # 6-3. 날씨 정보 가져오기
        daily_weather = get_weather_new(
            candidate.dest_lat,
            candidate.dest_lon,
            parsed_user_info.departure_datetime,
        )

        # 6-4. 실외 활동 적합도 점수 계산
        outdoor_score = calculate_outdoor_score(daily_weather)

        destination_candidate = DestinationCandidate(
            place_info=candidate,
            round_trip_hours=round_trip_hours_dict,
            daily_weather=daily_weather,
            outdoor_score=outdoor_score,
        )
        enriched_candidates.append(destination_candidate)

    print(
        f"6. {len(enriched_candidates)} enriched candidates after adding travel time and weather info"
    )

    # 7. top k 후보지 선정
    top_k_candidates = recommend_top_k_candidates(
        enriched_candidates,
        parsed_user_info.must_include or [],
        parsed_user_info.likes or [],
        k,
    )

    print(f"7. {len(top_k_candidates)} candidates after recommending top k")

    # 8. 세션 상태에 후보지 저장
    state.parsed_user_ifo = parsed_user_info
    state.candidates = top_k_candidates
    state.current_index = 0

    return top_k_candidates
