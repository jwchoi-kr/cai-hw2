import os
from datetime import datetime

from dotenv import load_dotenv

from utils.http import safe_get

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")


def get_round_trip_hours(departure_time, origin_lat, origin_lon, dest_lat, dest_lon):
    """
    출발 시각, 출발지, 목적지를 받고 왕복 이동 시간을 계산합니다.
    """
    url = "https://apis-navi.kakaomobility.com/v1/future/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    dt = datetime.fromisoformat(departure_time)
    params = {
        "departure_time": dt.strftime("%Y%m%d%H%M"),
        # lat lon 순서 주의
        "origin": f"{origin_lon},{origin_lat}",
        "destination": f"{dest_lon},{dest_lat}",
    }

    res = safe_get(url, headers=headers, params=params)

    round_trip_hours = (
        res["routes"][0]["summary"]["duration"] * 2 / 3600.0
    )  # 시간 단위로 변환

    return round_trip_hours
