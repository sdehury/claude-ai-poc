from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    """VADER-based sentiment analysis for financial headlines."""

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_texts(self, texts: list[str]) -> dict:
        """Analyze sentiment of a list of headlines/texts.

        Returns:
            {
                "score": float (-1 to 1),
                "label": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
                "positive_pct": float,
                "negative_pct": float,
                "neutral_pct": float,
                "num_articles": int,
                "details": list of per-headline scores
            }
        """
        if not texts:
            return {
                "score": 0.0,
                "label": "NEUTRAL",
                "positive_pct": 0,
                "negative_pct": 0,
                "neutral_pct": 100,
                "num_articles": 0,
                "details": [],
            }

        details = []
        compound_scores = []
        pos_count = neg_count = neu_count = 0

        for text in texts:
            scores = self.analyzer.polarity_scores(text)
            compound = scores["compound"]
            compound_scores.append(compound)

            if compound > 0.1:
                pos_count += 1
            elif compound < -0.1:
                neg_count += 1
            else:
                neu_count += 1

            details.append({
                "text": text[:100],
                "compound": round(compound, 3),
                "positive": round(scores["pos"], 3),
                "negative": round(scores["neg"], 3),
            })

        total = len(texts)
        avg_score = sum(compound_scores) / total

        if avg_score > 0.1:
            label = "POSITIVE"
        elif avg_score < -0.1:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {
            "score": round(avg_score, 3),
            "label": label,
            "positive_pct": round(pos_count / total * 100, 1),
            "negative_pct": round(neg_count / total * 100, 1),
            "neutral_pct": round(neu_count / total * 100, 1),
            "num_articles": total,
            "details": details,
        }
