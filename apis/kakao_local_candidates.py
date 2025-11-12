import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from dotenv import load_dotenv

from domain.enums import PlaceCategory
from domain.models import PlaceInfo
from utils.distance_helper import make_ring_centers
from utils.http import safe_get

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

MAX_KAKAO_RADIUS_M = 20_000.0
MAX_PAGES = 1
PAGE_SIZE = 15


def get_travel_candidates_by_keyword_in_radius(
    lat: float,
    lon: float,
    radius_m: float,
    keyword: str,
) -> List[PlaceInfo]:
    """
    주어진 위도/경도 주변에서 특정 키워드로 여행지 후보를 검색합니다.
    예: keyword="박물관", "전시회", "역사 유적" 등
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    radius_m = min(radius_m, MAX_KAKAO_RADIUS_M)  # 카카오 API의 최대 반경은 20km
    MAX_PAGES = 5
    PAGE_SIZE = 15

    all_places: List[PlaceInfo] = []

    for page in range(1, MAX_PAGES + 1):
        params = {
            "query": keyword,
            "x": lon,
            "y": lat,
            "radius": radius_m,
            "size": PAGE_SIZE,
            "page": page,
        }

        res = safe_get(url, headers=headers, params=params)
        if res is None:
            break

        documents = res.get("documents", [])
        if not documents:
            break

        for doc in documents:
            place_info = PlaceInfo(
                id=doc["id"],
                place_name=doc["place_name"],
                road_address_name=doc["road_address_name"],
                dest_lat=float(doc["y"]),
                dest_lon=float(doc["x"]),
            )
            all_places.append(place_info)

        if res.get("meta", {}).get("is_end", True):
            break

    return all_places


def get_travel_candidates_by_category_in_radius(
    lat: float,
    lon: float,
    radius_m: float,
    category_group_codes: List[PlaceCategory],
) -> List[PlaceInfo]:
    """
    주어진 위도/경도 주변의 여행지 후보를, 카테고리 기준으로 가져옵니다.
    카테고리는 관광명소 또는 문화시설로 제한됩니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/category"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    radius_m = min(radius_m, MAX_KAKAO_RADIUS_M)  # 카카오 API의 최대 반경은 20km

    all_places: List[PlaceInfo] = []

    # 여러 카테고리를 순회하며 병합
    for category in category_group_codes:
        category_code = category.value  # "AT4" 또는 "CT1"

        for page in range(1, MAX_PAGES + 1):
            params = {
                "category_group_code": category_code,
                "x": lon,
                "y": lat,
                "radius": radius_m,
                "size": PAGE_SIZE,
                "page": page,
            }

            res = safe_get(url, headers=headers, params=params)
            if res is None:
                break

            documents = res.get("documents", [])
            if not documents:
                break

            for doc in documents:
                place_info = PlaceInfo(
                    id=doc["id"],
                    place_name=doc["place_name"],
                    road_address_name=doc["road_address_name"],
                    dest_lat=float(doc["y"]),
                    dest_lon=float(doc["x"]),
                )
                all_places.append(place_info)

            if res.get("meta", {}).get("is_end", True):
                break

    return all_places


def get_travel_candidates_for_short_travel(
    origin_lat: float,
    origin_lon: float,
    radius_m: float,
    category_group_codes: List[PlaceCategory],
    keyword: Optional[str] = None,
) -> List[PlaceInfo]:
    """
    키워드가 주어졌다면 키워드 기반으로,
    그렇지 않다면 카테고리 기반으로 여행지 후보를 검색합니다.
    """
    if keyword and keyword.strip():
        # 키워드가 명확히 존재할 때 → 키워드 기반 검색
        return get_travel_candidates_by_keyword_in_radius(
            lat=origin_lat,
            lon=origin_lon,
            radius_m=radius_m,
            keyword=keyword.strip(),
        )
    else:
        # 키워드가 없거나 비어있을 때 → 카테고리 기반 검색
        return get_travel_candidates_by_category_in_radius(
            lat=origin_lat,
            lon=origin_lon,
            radius_m=radius_m,
            category_group_codes=category_group_codes,
        )


def get_travel_candidates_for_long_travel(
    origin_lat: float,
    origin_lon: float,
    radius_m: float,
    category_group_codes: List[PlaceCategory],
    keyword: Optional[str] = None,
) -> List[PlaceInfo]:
    """
    긴 여행 시간용:
    - 원점 1개 + 주변 6개 센터(총 7개 지점)에서 병렬로 장소를 찾아온다.
    """
    centers = make_ring_centers(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        radius_m=radius_m,
    )

    all_places: List[PlaceInfo] = []

    max_workers = min(7, len(centers))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_center = {
            executor.submit(
                get_travel_candidates_for_short_travel,
                lat,
                lon,
                MAX_KAKAO_RADIUS_M,  # 각 센터별 반경은 최대 20km로 고정
                category_group_codes,
                keyword,
            ): (lat, lon)
            for (lat, lon) in centers
        }

        for future in as_completed(future_to_center):
            try:
                places = future.result()
                all_places.extend(places)
            except Exception as e:
                print(
                    f"Error retrieving places for center {future_to_center[future]}: {e}"
                )

    # id 기준으로 중복 제거
    seen_ids: set[str] = set()
    unique_places: List[PlaceInfo] = []

    for place in all_places:
        if place.id in seen_ids:
            continue
        seen_ids.add(place.id)
        unique_places.append(place)

    return unique_places


def get_travel_candidates(
    origin_lat: float,
    origin_lon: float,
    radius_m: float,
    category_group_codes: List[PlaceCategory],
    keyword: Optional[str] = None,
) -> List[PlaceInfo]:
    """
    여행 시간에 따라 적절한 방법으로 여행지 후보를 검색합니다.
    """
    if radius_m > MAX_KAKAO_RADIUS_M:
        return get_travel_candidates_for_long_travel(
            origin_lat,
            origin_lon,
            radius_m,
            category_group_codes,
            keyword,
        )
    else:
        return get_travel_candidates_for_short_travel(
            origin_lat,
            origin_lon,
            radius_m,
            category_group_codes,
            keyword,
        )
