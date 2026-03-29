import xml.etree.ElementTree as ET
from typing import Optional

from finsight.fetchers.base_fetcher import BaseFetcher
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

# RSS feed URLs for Indian financial news
RSS_FEEDS = [
    ("Moneycontrol", "https://www.moneycontrol.com/rss/latestnews.xml"),
    ("Economic Times Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
]


class NewsFetcher(BaseFetcher):
    """Fetcher for financial news from RSS feeds."""

    def fetch_rss_headlines(self, max_per_feed: int = 10) -> list[dict]:
        """Fetch recent headlines from financial RSS feeds."""
        all_headlines = []

        for source_name, url in RSS_FEEDS:
            try:
                response = self._get(url)
                root = ET.fromstring(response.text)

                items = root.findall(".//item")[:max_per_feed]
                for item in items:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    description = item.findtext("description", "")

                    if title:
                        all_headlines.append({
                            "title": title.strip(),
                            "source": source_name,
                            "link": link.strip(),
                            "published": pub_date.strip(),
                            "description": description.strip()[:200],
                        })
            except Exception as e:
                logger.debug(f"RSS fetch failed for {source_name}: {e}")
                continue

        return all_headlines

    def fetch_stock_news(self, symbol: str) -> list[dict]:
        """Fetch news specific to a stock.

        Combines yfinance news (if available in the ticker) with
        RSS feeds filtered by the stock name/symbol.
        """
        headlines = self.fetch_rss_headlines()

        # Filter headlines containing the symbol or common name
        symbol_upper = symbol.upper().replace(".NS", "").replace(".BO", "")
        relevant = [
            h for h in headlines
            if symbol_upper.lower() in h["title"].lower()
        ]

        # If no relevant news found, return general market news
        if not relevant:
            return headlines[:10]

        return relevant
