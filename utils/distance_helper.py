import math
from typing import List, Optional, Tuple

from domain.enums import Transportation

MAX_KAKAO_RADIUS_M = 20_000.0


def max_travel_hours_to_radius_m(
    total_hours: float,
    transportation: Optional[Transportation] = None,
) -> float:
    """
    사용자의 총 여행 가능 시간(total_hours, 왕복 기준)과
    교통수단(Transportation Enum: CAR / PUBLIC)을 기반으로
    매우 naive한 탐색 반경(m)을 계산한다.

    이동 가능한 시간 비율은 대략 45%로 가정하고,
    왕복 이동 시간을 편도로 나눠 거리(km)로 환산해서
    마지막으로 안전 계수 0.8을 적용한다.

    최소 반경은 3 km(=3000 m)로 고정한다.
    """

    # 평균 이동 속도(km/h) — 매우 단순화된 값
    speed_map = {
        Transportation.CAR: 60.0,  # 시내/외 평균 속도 대략
        Transportation.PUBLIC: 22.0,  # 버스+지하철 평균치 (탑승/환승 포함)
    }

    # transport 값 없으면 car 기준으로 계산
    speed = speed_map.get(transportation, speed_map[Transportation.CAR])

    # 총 시간 중 실제 '이동'에 쓸 수 있는 시간 비율
    move_hours = max(0.0, total_hours) * 0.5

    # 왕복 → 편도로 나누기
    one_way_hours = move_hours / 2.0

    # 거리 = 속도 × 시간 (km)
    one_way_km = speed * one_way_hours

    # 약간의 여유 계수
    radius_km = max(3.0, one_way_km * 0.8)

    return radius_km * 1000.0  # meter


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
