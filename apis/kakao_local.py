import os
from typing import List

from dotenv import load_dotenv

from domain.models import PlaceInfo
from utils.http import safe_get

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")


def get_coords_by_address(address):
    """
    정확한 주소로부터 위도와 경도를 가져옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/address"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}

    res = safe_get(url, headers=headers, params=params)

    if res["documents"]:
        lat = res["documents"][0]["y"]
        lon = res["documents"][0]["x"]
        return lat, lon
    else:
        return None, None


def get_coords_by_keyword(keyword):
    """
    키워드(예: 서울대입구)로부터 위도와 경도를 가져옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": keyword, "size": 1}  # 결과 하나만 가져오기

    res = safe_get(url, headers=headers, params=params)

    if res["documents"]:
        lat = res["documents"][0]["y"]
        lon = res["documents"][0]["x"]
        return lat, lon
    else:
        return None, None


def get_coords(query):
    """
    주소 또는 키워드로부터 위도와 경도를 가져옵니다.
    """
    lat, lon = get_coords_by_address(query)  # 먼저 주소로 시도
    if lat is not None and lon is not None:
        return lat, lon

    lat, lon = get_coords_by_keyword(query)  # 키워드로 시도
    return lat, lon


def get_travel_candidates_by_distance(
    lat, lon, radius, category_group_code="AT4"
) -> List[PlaceInfo]:
    """
    주어진 위도와 경도 주변의 여행지 추천 장소를 가져옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/category"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "category_group_code": category_group_code,
        "x": lon,
        "y": lat,
        "radius": radius,
        "size": 10,  # 최대 10개 장소 추천
    }

    res = safe_get(url, headers=headers, params=params)

    candidates = []
    for doc in res["documents"]:
        place_info = PlaceInfo(
            place_name=doc["place_name"],
            address_name=doc["address_name"],
            road_address_name=doc["road_address_name"],
            phone=doc["phone"],
            distance=doc["distance"],
        )
        candidates.append(place_info)

    return candidates


def main():
    # 테스트용 메인 함수
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "서울대입구"
    lat, lon = get_coords(query)
    print(f"[TEST] {query} → lat={lat}, lon={lon}")


if __name__ == "__main__":
    main()
