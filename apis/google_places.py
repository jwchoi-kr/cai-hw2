import os

from dotenv import load_dotenv

from utils.http import safe_get, safe_post

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

BASE_URL = "https://places.googleapis.com/v1/places"


def search_place_id(query: str) -> str | None:
    """
    장소 이름으로 Google Places place_id 검색.
    예: "석촌호수", "남산타워", "롯데월드"
    """
    url = f"{BASE_URL}:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName",
    }

    body = {
        "textQuery": query,
    }

    # safe_post는 dict 또는 None을 반환함
    data = safe_post(url, headers=headers, json_body=body)

    if not data:
        print(f"TextSearch API 오류 또는 응답 없음: query={query}")
        return None

    places = data.get("places")
    if not places:
        print(f"No results for query: {query}")
        return None

    # 가장 첫 번째 결과의 place_id 반환
    return places[0]["id"]


def get_place_description(place_id: str) -> dict | None:
    """
    Google Places에서 장소 요약/설명(editorialSummary)만 가져옴.
    필요하면 리뷰(text)도 함께 담아 반환.

    반환 예시:
    {
        "summary": "A beautiful lake with walking paths ...",
        "reviews": ["리뷰1", "리뷰2", ...]  # optional
    }
    """
    url = f"{BASE_URL}/{place_id}"

    field_mask = ",".join(
        [
            "editorialSummary",
            "reviews.text",
        ]
    )

    headers = {
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": field_mask,
    }

    data = safe_get(url, headers=headers)
    if not data:
        print(f"Place description 응답 없음: place_id={place_id}")
        return None

    # editorialSummary: 장소 요약
    summary_text = None
    if "editorialSummary" in data and data["editorialSummary"]:
        summary_text = data["editorialSummary"].get("text")

    # reviews.text: 사용자 리뷰들
    reviews = []
    if "reviews" in data:
        for r in data["reviews"][:5]:  # 최대 5개 리뷰만
            text = (r.get("text") or {}).get("text")
            if text:
                reviews.append(text)

    return {
        "summary": summary_text,
        "reviews": reviews,
    }


def get_place_photos(place_id: str, max_photos: int = 3) -> list[str]:
    url = f"{BASE_URL}/{place_id}"
    headers = {"X-Goog-Api-Key": GOOGLE_API_KEY, "X-Goog-FieldMask": "photos"}

    data = safe_get(url, headers=headers)
    if not data or "photos" not in data:
        return []

    photos = data["photos"]
    resource_names = [p["name"] for p in photos[:max_photos]]
    return resource_names


def get_photo_url(photo_resource_name: str, max_size: int = 800) -> str | None:
    """
    Google Places photo 리소스 이름으로부터 실제 이미지 URL(photoUri)을 가져온다.
    """
    url = f"https://places.googleapis.com/v1/{photo_resource_name}/media"

    headers = {
        "X-Goog-Api-Key": GOOGLE_API_KEY,
    }

    params = {
        "maxHeightPx": max_size,
        "maxWidthPx": max_size,
        "skipHttpRedirect": "true",  # ← 이게 핵심
    }

    data = safe_get(url, headers=headers, params=params)
    if not data:
        return None

    # skipHttpRedirect=true 이면 JSON으로 { "photoUri": "..." } 형태가 온다.
    return data.get("photoUri")


def get_photo_urls(place_id: str, max_photos: int = 5) -> list[str]:
    resource_names = get_place_photos(place_id, max_photos)
    urls = []

    for name in resource_names:
        url = get_photo_url(name)
        if url:
            urls.append(url)

    return urls


if __name__ == "__main__":
    # 테스트 코드
    place_name = "남이섬"
    place_id = search_place_id(place_name)
    print(f"Place ID for '{place_name}': {place_id}")

    if place_id:
        description = get_place_description(place_id)
        print(f"Description for '{place_name}': {description}")

        photo_urls = get_photo_urls(place_id, max_photos=3)
        print(f"Photo URLs for '{place_name}': {photo_urls}")

        for url in photo_urls:
            print(f"Photo URL: {url}")
