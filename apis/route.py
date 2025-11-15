import os
from datetime import datetime

from dotenv import load_dotenv

from domain.enums import Transportation
from utils.http import safe_get

load_dotenv()

ODSAY_API_KEY = os.getenv("ODSAY_API_KEY")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")


def get_round_trip_hours_by_car(
    departure_datetime, origin_lat, origin_lon, dest_lat, dest_lon
):
    """
    출발 시각, 출발지, 목적지를 받고 왕복 이동 시간을 계산합니다.
    """
    url = "https://apis-navi.kakaomobility.com/v1/future/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    dt = datetime.fromisoformat(departure_datetime)
    params = {
        "departure_time": dt.strftime("%Y%m%d%H%M"),
        # lat lon 순서 주의
        "origin": f"{origin_lon},{origin_lat}",
        "destination": f"{dest_lon},{dest_lat}",
    }

    res = safe_get(url, headers=headers, params=params)

    round_trip_hours = (
        (res["routes"][0]["summary"]["duration"] * 2 / 3600.0)
        if res["routes"][0]["result_code"] == 0
        else 1
    )

    return round_trip_hours


def get_round_trip_hours_by_public(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    ODsay 대중교통 API를 사용해
    출발 시각, 출발지, 목적지를 받고 왕복 대중교통 이동 시간을 계산합니다.

    반환:
        왕복 소요 시간(시간 단위, float)
        - API 실패 또는 경로 없음 시, 기본값 1시간 반환
    """
    # ODsay는 departure_datetime을 직접 받지는 않지만,
    # 시각에 따라 경로가 달라질 수 있는 여지를 고려하려면 나중에 추가 옵션 사용 가능.
    # 지금은 좌표 기반 기본 경로만 사용.
    url = "https://api.odsay.com/v1/api/searchPubTransPathT"

    params = {
        "apiKey": ODSAY_API_KEY,
        "SX": origin_lon,  # 경도
        "SY": origin_lat,  # 위도
        "EX": dest_lon,  # 경도
        "EY": dest_lat,  # 위도
    }

    try:
        res = safe_get(url, params=params)
    except Exception as e:
        print("ODsay API 호출 오류:", e)
        return 1.0  # fallback

    # 기본 구조 체크
    result = res.get("result")
    if not result:
        print("ODsay: result 없음:", res)
        return 1.0

    path_list = result.get("path")
    if not path_list:
        print("ODsay: path 없음:", result)
        return 1.0

    # 첫 번째 경로를 최적 경로로 사용
    best_path = path_list[0]
    info = best_path.get("info")
    if not info:
        print("ODsay: info 없음:", best_path)
        return 1.0

    # totalTime: 편도 소요 시간(분 단위)
    total_time_min = info.get("totalTime")
    if total_time_min is None:
        print("ODsay: totalTime 없음:", info)
        return 1.0

    # 왕복 시간(시간 단위)로 변환
    round_trip_hours = (total_time_min * 2) / 60.0
    return round_trip_hours


def get_round_trip_hours(
    transportation: Transportation | None,
    departure_datetime: str,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> dict[Transportation, float | None]:
    """
    교통수단에 따라 왕복 소요 시간을 계산한다.

    리턴 타입:
    {
        "car": float | None,
        "public": float | None
    }

    - transportation == CAR → car만 호출
    - transportation == PUBLIC → public만 호출
    - transportation == None → 둘 다 호출
    """

    result = {
        Transportation.CAR: None,
        Transportation.PUBLIC: None,
    }

    # CAR 요청
    if transportation in (None, Transportation.CAR):
        result[Transportation.CAR] = get_round_trip_hours_by_car(
            departure_datetime, origin_lat, origin_lon, dest_lat, dest_lon
        )

    # PUBLIC 요청
    if transportation in (None, Transportation.PUBLIC):
        result[Transportation.PUBLIC] = get_round_trip_hours_by_public(
            origin_lat, origin_lon, dest_lat, dest_lon
        )

    return result
