import os

from dotenv import load_dotenv

from utils.http import safe_get

load_dotenv()

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")


def get_coords_by_address(address) -> tuple[float | None, float | None]:
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
        return float(lat), float(lon)
    else:
        return None, None


def get_coords_by_keyword(keyword) -> tuple[float | None, float | None]:
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
        return float(lat), float(lon)
    else:
        return None, None


def get_coords(query) -> tuple[float | None, float | None]:
    """
    주소 또는 키워드로부터 위도와 경도를 가져옵니다.
    """
    lat, lon = get_coords_by_address(query)  # 먼저 주소로 시도
    if lat is not None and lon is not None:
        return lat, lon

    lat, lon = get_coords_by_keyword(query)  # 키워드로 시도
    return lat, lon
