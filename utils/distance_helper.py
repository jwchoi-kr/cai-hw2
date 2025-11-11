import math
from typing import List, Optional, Tuple

MAX_KAKAO_RADIUS_M = 20_000.0


def time_to_radius_m(hours: float, transportation: Optional[str] = "car") -> float:
    """
    총 가용시간 -> 탐색 '반경(m)'으로 변환 (매우 나이브).
    이동에 45% 사용, 편도 기준 절반, 여유 0.8 배.
    """
    speed_map = {
        "car": 60.0,
        "bus": 40.0,
        "train": 80.0,
        "bicycle": 15.0,
        "walking": 5.0,
        "public": 22.0,  # 없을 때 기본
    }
    key = (transportation or "public").lower()
    speed = speed_map.get(key, 22.0)
    move_hours = max(0.0, hours) * 0.45
    one_way_km = (speed * move_hours) / 2.0
    radius_km = max(3.0, one_way_km * 0.8)
    radius_m = radius_km * 1000.0
    return radius_m


def make_ring_centers(
    origin_lat: float,
    origin_lon: float,
    radius_m: float,
) -> List[Tuple[float, float]]:
    """
    반경이 큰 경우, 여러 중심점을 만들어서 병렬로 장소를 검색하기 위한 헬퍼.
    60도 간격으로 6개 중심점을 원형으로 배치함.
    origin도 포함해서 총 7개 중심점이 됨.

    - 입력 radius_m는 "탐색하고 싶은 전체 반경(미터)".
    - 하지만 ring center와 원점 사이 거리는
      Kakao API의 최대 radius(20km)를 넘지 않도록 클램프한다.
      => 너무 멀리 떨어져서 원 사이에 구멍 나는 것을 방지.
    """

    if radius_m <= MAX_KAKAO_RADIUS_M:
        return []

    effective_radius_m = min(radius_m, 2 * MAX_KAKAO_RADIUS_M)
    center_distance = effective_radius_m - MAX_KAKAO_RADIUS_M

    # 위/경도 계산은 km 단위로 할 거라 km로 변환
    center_distance_km = max(0.0, center_distance) / 1000.0

    centers: List[Tuple[float, float]] = []
    # origin 추가
    centers.append((origin_lat, origin_lon))

    for deg in range(0, 360, 60):
        rad = math.radians(deg)
        delta_lat = (center_distance_km * math.cos(rad)) / 110.574
        delta_lon = (center_distance_km * math.sin(rad)) / (
            111.320 * math.cos(math.radians(origin_lat))
        )
        lat = origin_lat + delta_lat
        lon = origin_lon + delta_lon
        centers.append((lat, lon))

    return centers
