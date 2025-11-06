from typing import Optional


def time_to_radius(hours: float, transportation: Optional[str]) -> float:
    """
    총 가용시간 -> 탐색 '반경(km)'으로 변환 (매우 나이브).
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
