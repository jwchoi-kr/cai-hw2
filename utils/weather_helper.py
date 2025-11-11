import datetime
import math
from typing import Tuple


def latlon_to_xy(lat, lon):
    """
    위도/경도 -> 기상청 격자 좌표 변환
    """
    RE = 6371.00877  # 지구 반경(km)
    GRID = 5.0  # 격자 간격(km)
    SLAT1 = 30.0  # 투영 위도1
    SLAT2 = 60.0  # 투영 위도2
    OLON = 126.0  # 기준점 경도
    OLAT = 38.0  # 기준점 위도
    XO = 43  # 기준점 X좌표
    YO = 136  # 기준점 Y좌표

    DEGRAD = math.pi / 180.0

    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf**sn * math.cos(slat1)) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro**sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra**sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = ra * math.sin(theta) + XO + 0.5
    y = ro - ra * math.cos(theta) + YO + 0.5
    return int(x), int(y)


def get_kma_base_datetime_from_input(input_iso: str) -> Tuple[str, str]:
    """
    유저가 입력한 ISO 형식 시각(YYYY-MM-DDTHH:MM:SS)을 바탕으로
    기상청 단기예보(getVilageFcst)용 base_date, base_time을 계산한다.

    예:
        input_iso="2025-11-10T15:30:00" → base_date="20251110", base_time="1400"

    기상청 발표 시각: 02, 05, 08, 11, 14, 17, 20, 23시
    """
    # ISO 문자열을 datetime 객체로 변환
    target_dt = datetime.datetime.fromisoformat(input_iso)

    BASE_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]
    hour = target_dt.hour

    # target_dt보다 이전 또는 같은 발표 시각 중 가장 최근 발표 시각 찾기
    candidates = [h for h in BASE_HOURS if h <= hour]

    if candidates:
        base_hour = max(candidates)
        base_date_dt = target_dt
    else:
        # 첫 발표 시각(02:00) 이전이면 전날 23시 발표 사용
        base_hour = 23
        base_date_dt = target_dt - datetime.timedelta(days=1)

    base_date = base_date_dt.strftime("%Y%m%d")
    base_time = f"{base_hour:02d}00"  # HHMM 형식

    return base_date, base_time
