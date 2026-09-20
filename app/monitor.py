import time

import httpx


def check_endpoint(url: str) -> dict:
    start_time = time.perf_counter()

    try:
        response = httpx.get(
            url,
            timeout=10.0,
            follow_redirects=True,
        )

        response_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        is_healthy = 200 <= response.status_code < 400

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "error": None,
        }

    except httpx.RequestError as exc:
        response_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        return {
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": response_time_ms,
            "error": str(exc),
        }