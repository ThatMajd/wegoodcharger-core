"""Shared entry point for HTTP requests, debugging, and routing changes."""

import logging
from time import perf_counter

import requests

USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) uni-app"
DEFAULT_BASE_URL = "https://ev.weguyun.com"

logger = logging.getLogger(__name__)


def request_raw(method: str, url: str, **kwargs) -> requests.Response:
    """Forward all options to requests.request and return its response unchanged.

    Make shared routing changes here before dispatching the request. Enable this
    module's DEBUG logging to see request URLs, status codes, and elapsed times.
    Request bodies and headers are not logged.
    """
    started = perf_counter()
    logger.debug("HTTP %s %s", method, url)
    try:
        response = requests.request(method, url, **kwargs)
    except requests.RequestException:
        logger.debug(
            "HTTP %s %s failed after %.3fs",
            method,
            url,
            perf_counter() - started,
            exc_info=True,
        )
        raise

    logger.debug(
        "HTTP %s %s -> %s in %.3fs",
        method,
        url,
        response.status_code,
        perf_counter() - started,
    )
    return response

def build_headers(token: str ):
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
