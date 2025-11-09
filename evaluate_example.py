#%%
from datetime import datetime, timedelta

from apis.openai_parser import client
from utils.metrics import mrr_score, hit_at_k
from domain.enums import AirQualityGrade, WeatherCondition
from services.travel_recommendation_service import generate_recommendation
from domain.models import (
    PlaceInfo,
    WeatherSnapshot,
    WeatherInfo,
    DestinationCandidate,
)


def mrr_score(pred_item, gold_ranking):
    """
    pred_item: 모델이 예측한 아이템 (예: "item_10")
    gold_ranking: 사람이 매긴 순위 리스트 (예: ["item_1", "item_2", "item_3"])
    """
    if pred_item not in gold_ranking:
        return 0.0
    rank = gold_ranking.index(pred_item) + 1  # 1-based
    return 1 / rank


def hit_at_k(pred_item, gold_ranking, k=3):
    """
    pred_item: 모델이 예측한 아이템 (예: "item_10")
    gold_ranking: 사람이 매긴 순위 리스트 (예: ["item_1", "item_2", "item_3"])
    """
    return 1.0 if pred_item in gold_ranking[:k] else 0.0


#%%
# 샘플 데이터 생성

user_input = "지금 당장 당일치기 여행을 떠날거야. 서울대입구에서 출발해서 산책하기 좋은, 맑은 날씨의 여행지를 추천해줘. 4시간 내로 왕복 가능해야하고, 자연 경관이 아름다우면서 조용하면 좋겠어."
print("\n=== User input ===")
print(user_input)

now = datetime.now()
candidate1 = DestinationCandidate(
    place_info=PlaceInfo(
        place_name="남이섬",
        address_name="강원 춘천시 남산면 남이섬길 1",
        road_address_name="강원 춘천시 남산면 남이섬길 1",
        phone="033-222-2000",
        distance_m=78000.0,
    ),
    weather=WeatherInfo(
        current=WeatherSnapshot(
            timestamp=now,
            weather_condition=WeatherCondition.CLEAR,
            temperature=15.0,
            humidity_percent=40.0,
            wind_speed_m_s=2.3,
            air_quality=AirQualityGrade.GOOD,
        ),
        hourly_forecast=[
            WeatherSnapshot(
                timestamp=now + timedelta(hours=i),
                weather_condition=WeatherCondition.PARTLY_CLOUDY if i < 3 else WeatherCondition.CLOUDY,
                temperature=15.0 + 0.3 * i,
                humidity_percent=45 - i,
                wind_speed_m_s=2.3 + 0.2 * i,
                air_quality=AirQualityGrade.GOOD,
            )
            for i in range(1, 5)
        ],
    ),
    round_trip_hours=3.5,
    reasons=[
        "서울에서 약 2시간 거리로 당일치기 여행에 적합함",
        "맑고 쾌적한 날씨로 야외활동하기 좋음",
        "호수와 단풍으로 유명한 자연 힐링 명소",
    ],
)
candidate2 = DestinationCandidate(
    place_info=PlaceInfo(
        place_name="안목해변",
        address_name="강원 강릉시 창해로 17",
        road_address_name="강원 강릉시 창해로 17",
        phone="033-660-2023",
        distance_m=220000.0,
    ),
    weather=WeatherInfo(
        current=WeatherSnapshot(
            timestamp=now,
            weather_condition=WeatherCondition.PARTLY_CLOUDY,
            temperature=18.2,
            humidity_percent=55.0,
            wind_speed_m_s=3.1,
            air_quality=AirQualityGrade.NORMAL,
        ),
        hourly_forecast=[
            WeatherSnapshot(
                timestamp=now + timedelta(hours=i),
                weather_condition=WeatherCondition.CLOUDY if i >= 3 else WeatherCondition.PARTLY_CLOUDY,
                temperature=18.2 - 0.2 * i,
                humidity_percent=55 + 2 * i,
                wind_speed_m_s=3.1 + 0.1 * i,
                air_quality=AirQualityGrade.NORMAL,
            )
            for i in range(1, 5)
        ],
    ),
    round_trip_hours=6.0,
    reasons=[
        "동해안 대표 카페거리로 여유로운 분위기",
        "맑은 바다 전망과 시원한 해풍",
        "날씨가 선선해 산책이나 드라이브에 적합함",
    ],
)
candidate3 = DestinationCandidate(
    place_info=PlaceInfo(
        place_name="아침고요수목원",
        address_name="경기 가평군 상면 수목원로 432",
        road_address_name="경기 가평군 상면 수목원로 432",
        phone="1544-6703",
        distance_m=65000.0,
    ),
    weather=WeatherInfo(
        current=WeatherSnapshot(
            timestamp=now,
            weather_condition=WeatherCondition.HEAVY_RAIN,
            temperature=13.7,
            humidity_percent=95.0,
            wind_speed_m_s=1.8,
            air_quality=AirQualityGrade.GOOD,
        ),
        hourly_forecast=[
            WeatherSnapshot(
                timestamp=now + timedelta(hours=i),
                weather_condition=WeatherCondition.HEAVY_RAIN,
                temperature=13.7 + 0.1 * i,
                humidity_percent=95.0,
                wind_speed_m_s=1.8 + 0.1 * i,
                air_quality=AirQualityGrade.GOOD,
            )
            for i in range(1, 5)
        ],
    ),
    round_trip_hours=1.0,
    reasons=[
        "서울에서 90분 거리로 접근성 우수",
        "조용하고 아름다운 정원 산책로",
        "가족 및 연인과 함께하기 좋은 힐링 코스",
    ],
)
destination_candidates = [candidate1, candidate2, candidate3]

print("\n=== Sample candidates ===")
for d in destination_candidates:
    print(f"{d.place_info.place_name}:" 
        f" {d.weather.current.weather_condition},"
        f" {d.round_trip_hours} hours round trip")
    
gold = ["남이섬", "안목해변", "아침고요수목원"]
print("\n=== Gold rank ===")
print(gold)
#%%
# 우리 방법: 외부 APIs로 거리, 날씨 등 고려해 추천
output_ours, place_ours = generate_recommendation(
    user_input, destination_candidates)
print("\n=== Recommendation by ours ===")
print(f"추천 여행지: {place_ours}")
print(output_ours)
print("MRR:", mrr_score(place_ours, gold), 
      "Hit@2:", hit_at_k(place_ours, gold, k=2))
# %%
# 베이스라인-Naive: 외부 APIs 없이 GPT-4o-mini만 사용
def baseline_naive(
    user_input: str) -> tuple[str, str]:

    prompt = f"""
    당신은 유용한 여행 추천 전문가입니다.
    [사용자 요청]을 바탕으로 가장 적절한 여행지 한 곳을 추천해주고, 
    그 근처 음식점도 하나만 함께 추천해주세요.
    description에는 추천할 여행지와, 현재 날씨, 추천하는 이유, 음식점을 포함하여
    해당 여행지를 사용자에게 추천하는 문구를 작성하세요.
    따뜻하고 친근한 말투로 여행지를 추천하고, 
    텍스트는 여행 블로그나 가이드북처럼 자연스럽고 부드럽게 표현되어야 합니다.

    [사용자 요청]
    {user_input}

    출력 형식은 다음 JSON 형태로만 답변하세요:
    {{
        "place_name": "<추천 여행지 이름>",
        "description": "<추천지, 현재 날씨, 추천 이유, 근처 음식점>"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    import json

    content = response.choices[0].message.content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return None, None

    destination_final_name = result["place_name"]
    output = result["description"]

    return output, destination_final_name


output_baseline_naive, place_baseline_naive = baseline_naive(user_input)
print("\n=== Recommendation by baseline_naive ===")
print(f"추천 여행지: {place_baseline_naive}")
print(output_baseline_naive)
print("MRR:", mrr_score(place_baseline_naive, gold), 
      "Hit@2:", hit_at_k(place_baseline_naive, gold, k=2))
# %%
# 베이스라인-Distance: 거리 기반 후보군 활용
def baseline_distance(
    user_input: str, destination_candidates: list[DestinationCandidate]
) -> tuple[str, str]:

    candidates_text = ""
    for i, candidate in enumerate(destination_candidates):
        candidates_text += \
            f"여행지 {i+1}. {candidate.place_info.place_name}: " \
            f"{candidate.round_trip_hours}시간 왕복 거리 \n"

    prompt = f"""
    당신은 유용한 여행 추천 전문가입니다.
    [사용자 요청]을 바탕으로 가장 적절한 여행지 한 곳을 추천해주고, 
    그 근처 음식점도 하나만 함께 추천해주세요.
    description에는 추천할 여행지와, 현재 날씨, 추천하는 이유, 음식점을 포함하여
    해당 여행지를 사용자에게 추천하는 문구를 작성하세요.
    따뜻하고 친근한 말투로 여행지를 추천하고, 
    텍스트는 여행 블로그나 가이드북처럼 자연스럽고 부드럽게 표현되어야 합니다.

    [사용자 요청]
    {user_input}

    [여행지 후보]
    {candidates_text}

    출력 형식은 다음 JSON 형태로만 답변하세요:
    {{
        "place_name": "<추천 여행지 이름>",
        "description": "<추천지, 현재 날씨, 추천 이유, 근처 음식점>"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    import json

    content = response.choices[0].message.content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return None, None
    
    destination_final_name = result["place_name"]
    output = result["description"]

    return output, destination_final_name


output_baseline_distance, place_baseline_distance = \
    baseline_distance(user_input, destination_candidates)
print("\n=== Recommendation by baseline_distance ===")
print(f"추천 여행지: {place_baseline_distance}")
print(output_baseline_distance)
print("MRR:", mrr_score(place_baseline_distance, gold), 
      "Hit@2:", hit_at_k(place_baseline_distance, gold, k=2))
# %%