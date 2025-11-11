import requests
from requests.exceptions import HTTPError, RequestException


def safe_get(url, headers=None, params=None, timeout: int = 5):
    """
    안전하게 GET 요청을 보내고 JSON 응답을 반환합니다.
    - 성공: res.json() 반환
    - 실패: 에러 로그 출력 후 None 반환
    """
    try:
        res = requests.get(url, headers=headers, params=params, timeout=timeout)
        res.raise_for_status()
        return res.json()

    except HTTPError as e:
        status = e.response.status_code if e.response is not None else "N/A"
        print(f"[API HTTP error] {url} -> {status} {e}")

        if e.response is not None:
            try:
                print("[API error body]:", e.response.text)
            except Exception:
                pass

        return None

    except RequestException as e:
        print(f"[API request error] {url} -> {e}")
        return None
