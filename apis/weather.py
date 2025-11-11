import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from domain.models import (
    RawWeather,
    WeatherCondition,
    WeatherSnapshot,
    WeatherSummary,
)
from utils.http import safe_get
from utils.weather_helper import (
    get_kma_base_datetime_from_input,
    latlon_to_xy,
)

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def get_raw_weather(
    lat: float,
    lon: float,
    input_iso: str,
    duration_hours: int,
) -> RawWeather:
    """
    주어진 위도/경도 기준으로,
    기상청 단기예보(getVilageFcst)에서 base_date/base_time 이후 duration_hours 동안의
    시간별 날씨를 가져와 RawWeather 형태로 반환한다.
    """
    nx, ny = latlon_to_xy(lat, lon)  # 위경도를 기상청 격자 좌표로 변환
    base_date, base_time = get_kma_base_datetime_from_input(input_iso)

    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": WEATHER_API_KEY,
        "numOfRows": 200,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,  # YYYYMMDD
        "base_time": base_time,  # HHMM
        "nx": nx,
        "ny": ny,
    }

    print(json.dumps(params, indent=2, ensure_ascii=False))
    res = safe_get(url, params=params)
    # 실패하면 비어있는 RawWeather 반환
    if res is None:
        return RawWeather(nx=nx, ny=ny, snapshots=[])

    items = res["response"]["body"]["items"]["item"]

    # 보고 싶은 시간 구간: [base_datetime, base_datetime + duration_hours]
    start_dt = datetime.strptime(base_date + base_time, "%Y%m%d%H%M")
    end_dt = start_dt + timedelta(hours=duration_hours)

    # TMP: 기온, SKY: 하늘상태, PTY: 강수형태, POP: 강수확률
    target_categories = {"TMP", "SKY", "PTY", "POP"}

    # dt별로 TMP/SKY/PTY/POP를 모아두는 버킷
    bucket: Dict[datetime, Dict[str, Any]] = {}

    for item in items:
        fcst_date = item["fcstDate"]  # "20250110"
        fcst_time = item["fcstTime"]  # "0900"
        category = item["category"]  # "TMP" / "PTY" / "SKY" / "POP"
        value = item["fcstValue"]

        if category not in target_categories:
            continue

        fcst_dt = datetime.strptime(fcst_date + fcst_time, "%Y%m%d%H%M")

        if fcst_dt < start_dt or fcst_dt > end_dt:
            continue

        if fcst_dt not in bucket:
            bucket[fcst_dt] = {
                "dt": fcst_dt,
            }

        bucket[fcst_dt][category] = value

    # 시간 순으로 정렬해서 WeatherSnapshot 리스트로 변환
    snapshots: List[WeatherSnapshot] = []
    for dt_key in sorted(bucket.keys()):
        row = bucket[dt_key]

        def _to_float(v: Optional[str]) -> Optional[float]:
            if v is None:
                return None
            try:
                return float(v)
            except ValueError:
                return None

        def _to_int(v: Optional[str]) -> Optional[int]:
            if v is None:
                return None
            try:
                return int(v)
            except ValueError:
                return None

        snapshot = WeatherSnapshot(
            dt=row["dt"],
            TMP=_to_float(row.get("TMP")),
            SKY=_to_int(row.get("SKY")),
            PTY=_to_int(row.get("PTY")),
            POP=_to_int(row.get("POP")),
        )
        snapshots.append(snapshot)

    return RawWeather(nx=nx, ny=ny, snapshots=snapshots)


def summarize_weather(raw: RawWeather) -> WeatherSummary:
    """
    RawWeather(시간별 스냅샷들)를 받아서
    - 평균 기온
    - 대표 날씨(WeatherCondition)
    로 요약한다.
    """
    snapshots = raw.snapshots
    if not snapshots:
        # 데이터가 없으면 그냥 맑고 10도로 처리
        return WeatherSummary(
            weather_condition=WeatherCondition.CLEAR,
            temperature=10.0,
        )

    # 1) 평균 기온 계산
    temps = [s.TMP for s in snapshots if s.TMP is not None]
    avg_temp = sum(temps) / len(temps) if temps else 10.0

    # 2) 강수 여부 / 형태 먼저 보고, 없으면 하늘 상태(SKY)로 판단
    precip_codes = [s.PTY for s in snapshots if s.PTY is not None and s.PTY != 0]

    if precip_codes:
        # 강수형태 우선순위: 눈 > 비/눈 > 비 > 이슬비
        if any(c in (3, 7) for c in precip_codes):
            condition = WeatherCondition.SNOW
        elif any(c in (2, 6) for c in precip_codes):
            condition = WeatherCondition.RAIN_SNOW
        elif any(c == 5 for c in precip_codes):
            condition = WeatherCondition.DRIZZLE
        else:
            # PTY == 1 (비) 또는 기타 값
            condition = WeatherCondition.RAIN
    else:
        # 강수 없으면 SKY 코드 기반으로 결정
        sky_codes = [s.SKY for s in snapshots if s.SKY is not None]
        if sky_codes:
            # 최빈값 사용
            sky_mode = max(set(sky_codes), key=sky_codes.count)
        else:
            sky_mode = 1  # 기본 맑음

        if sky_mode == 1:
            condition = WeatherCondition.CLEAR
        elif sky_mode == 3:
            condition = WeatherCondition.PARTLY_CLOUDY
        elif sky_mode == 4:
            condition = WeatherCondition.OVERCAST
        else:
            # 혹시 모르는 값은 그냥 흐림으로
            condition = WeatherCondition.CLOUDY

    return WeatherSummary(
        weather_condition=condition,
        temperature=avg_temp,
    )


def get_weather_summary(
    lat: float,
    lon: float,
    input_iso: str,
    duration_hours: int,
) -> WeatherSummary:
    """
    위도/경도와 기준 시점, 기간을 받아서
    해당 위치의 요약된 날씨 정보를 반환한다.
    """

    raw_weather = get_raw_weather(
        lat=lat,
        lon=lon,
        input_iso=input_iso,
        duration_hours=duration_hours,
    )
    summary = summarize_weather(raw_weather)
    return summary
