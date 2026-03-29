from abc import ABC, abstractmethod
import httpx
from finsight.utils.rate_limiter import RateLimiter
from finsight.utils.logger import get_logger


class BaseFetcher(ABC):
    """Abstract base class for all data fetchers."""

    def __init__(self, rate_limit: float = 2.0, burst: int = 5):
        self.logger = get_logger(self.__class__.__name__)
        self.rate_limiter = RateLimiter(rate=rate_limit, burst=burst)
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

    def _get(self, url: str, **kwargs) -> httpx.Response:
        """Rate-limited GET request."""
        self.rate_limiter.acquire()
        self.logger.debug(f"GET {url}")
        response = self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def _get_json(self, url: str, **kwargs) -> dict | list:
        """Rate-limited GET request that returns parsed JSON."""
        return self._get(url, **kwargs).json()

    def close(self):
        """Clean up HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
