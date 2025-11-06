import requests
from requests.exceptions import RequestException


def safe_get(url, headers=None, params=None):
    """
    안전하게 GET 요청을 보내고 JSON 응답을 반환합니다.
    실패 시 None을 반환합니다.
    """
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()
    except RequestException as e:
        print(f"[API error] {url} -> {e}")
        return None
