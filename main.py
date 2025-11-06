from services.travel_intent_service import generate_travel_candidates


def main():
    # user_input = input("여행 계획을 입력하세요: ")
    user_input = "서울대입구에서 출발하여 자동차로 5시간 이내에 갈 수 있는 여행지를 추천해줘. 자연 경관이 아름답고, 조용한 곳이면 좋겠어."

    try:
        candidates = generate_travel_candidates(user_input)
        print("추천 여행지:")
        for idx, place in enumerate(candidates, start=1):
            print(f"{idx}. {place.place_name} - {place.address_name} ")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
