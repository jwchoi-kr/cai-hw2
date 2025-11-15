import requests
from requests.exceptions import HTTPError, RequestException

DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 15


def safe_get(url, headers=None, params=None, timeout: int | tuple = None):
    """
    안전하게 GET 요청을 보내고 JSON 응답을 반환합니다.
    - timeout: int 또는 (connect_timeout, read_timeout) 튜플
      기본값은 (5초 연결, 15초 읽기)
    """
    try:
        # timeout 설정 처리
        if timeout is None:
            timeout_tuple = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
        elif isinstance(timeout, int):
            timeout_tuple = (DEFAULT_CONNECT_TIMEOUT, timeout)
        else:
            timeout_tuple = timeout  # (conn, read)

        res = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout_tuple,
        )
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


def safe_post(
    url, headers=None, json_body=None, data=None, timeout: int | tuple = None
):
    """
    안전하게 POST 요청을 보내고 JSON 응답을 반환합니다.
    - timeout: int 또는 (connect_timeout, read_timeout)
      기본값은 (5초 연결, 15초 읽기)
    """
    try:
        # timeout 설정 처리
        if timeout is None:
            timeout_tuple = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
        elif isinstance(timeout, int):
            timeout_tuple = (DEFAULT_CONNECT_TIMEOUT, timeout)
        else:
            timeout_tuple = timeout  # (conn, read)

        res = requests.post(
            url,
            headers=headers,
            json=json_body,
            data=data,
            timeout=timeout_tuple,
        )
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
