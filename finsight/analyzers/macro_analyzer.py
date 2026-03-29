from typing import Optional
from finsight.utils.helpers import score_linear, average_non_none
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

# Sector sensitivity to macro factors
# Positive value = tailwind when factor is high, negative = headwind
SECTOR_SENSITIVITY = {
    "Technology": {
        "usd_strength": 0.8,    # IT companies earn in USD
        "interest_rate": -0.3,
        "gdp_growth": 0.5,
        "oil_price": -0.1,
    },
    "Financial Services": {
        "interest_rate": 0.7,   # Banks benefit from rate hikes
        "gdp_growth": 0.8,
        "inflation": -0.4,
        "oil_price": -0.2,
    },
    "Healthcare": {
        "usd_strength": 0.5,   # Pharma exports
        "gdp_growth": 0.3,
        "interest_rate": -0.1,
        "oil_price": -0.1,
    },
    "Consumer Defensive": {
        "gdp_growth": 0.6,
        "inflation": -0.5,     # Margin pressure
        "interest_rate": -0.2,
        "oil_price": -0.3,
    },
    "Consumer Cyclical": {
        "gdp_growth": 0.8,
        "inflation": -0.4,
        "interest_rate": -0.5,
        "oil_price": -0.4,
    },
    "Industrials": {
        "gdp_growth": 0.9,
        "govt_capex": 0.8,
        "interest_rate": -0.3,
        "oil_price": -0.3,
    },
    "Energy": {
        "oil_price": 0.9,
        "gdp_growth": 0.4,
        "interest_rate": -0.1,
        "inflation": 0.2,
    },
    "Basic Materials": {
        "gdp_growth": 0.7,
        "china_demand": 0.6,
        "interest_rate": -0.2,
        "oil_price": -0.2,
    },
    "Utilities": {
        "interest_rate": -0.5,
        "gdp_growth": 0.3,
        "oil_price": -0.3,
        "inflation": -0.3,
    },
    "Communication Services": {
        "gdp_growth": 0.5,
        "interest_rate": -0.3,
        "oil_price": -0.1,
        "inflation": -0.2,
    },
    "Real Estate": {
        "interest_rate": -0.8,
        "gdp_growth": 0.7,
        "inflation": -0.3,
        "oil_price": -0.1,
    },
}

# Macro factor scoring (current conditions -> score)
# Higher score = more favorable
MACRO_CONDITION_SCORING = {
    "gdp_growth": (2.0, 8.0),       # India GDP: 2% bad, 8% great
    "inflation": (8.0, 3.0),         # Lower inflation is better
    "interest_rate": (8.0, 5.0),     # Moderate rates are better
}


class MacroAnalyzer:
    """Sector-level macro environment scoring."""

    def analyze_sector(
        self,
        sector: str,
        macro_data: Optional[dict] = None,
    ) -> dict:
        """Score macro environment for a given sector.

        Args:
            sector: yfinance sector name
            macro_data: dict with keys like 'india_gdp_growth', 'india_inflation'

        Returns:
            {
                "sector": str,
                "macro_score": float (0-100),
                "tailwinds": list[str],
                "headwinds": list[str],
                "assessment": str,
            }
        """
        sensitivities = SECTOR_SENSITIVITY.get(sector, {})
        if not sensitivities:
            # Try partial match
            for key, val in SECTOR_SENSITIVITY.items():
                if key.lower() in sector.lower() or sector.lower() in key.lower():
                    sensitivities = val
                    break

        tailwinds = []
        headwinds = []

        if not macro_data:
            return {
                "sector": sector,
                "macro_score": 50.0,
                "tailwinds": ["Macro data unavailable — defaulting to neutral"],
                "headwinds": [],
                "assessment": "NEUTRAL (insufficient data)",
            }

        # Score based on available macro data and sector sensitivity
        factor_scores = []

        gdp = macro_data.get("india_gdp_growth")
        if gdp is not None:
            gdp_score = score_linear(gdp, *MACRO_CONDITION_SCORING["gdp_growth"])
            if gdp_score is not None:
                sensitivity = sensitivities.get("gdp_growth", 0.5)
                factor_scores.append(gdp_score * abs(sensitivity))
                if gdp > 6 and sensitivity > 0:
                    tailwinds.append(f"Strong India GDP growth ({gdp:.1f}%) benefits {sector}")
                elif gdp < 5 and sensitivity > 0:
                    headwinds.append(f"Slowing GDP growth ({gdp:.1f}%) impacts {sector}")

        inflation = macro_data.get("india_inflation")
        if inflation is not None:
            inf_score = score_linear(inflation, *MACRO_CONDITION_SCORING["inflation"])
            if inf_score is not None:
                sensitivity = abs(sensitivities.get("inflation", 0.3))
                factor_scores.append(inf_score * sensitivity)
                if inflation > 6:
                    headwinds.append(f"High inflation ({inflation:.1f}%) pressures margins")
                elif inflation < 4:
                    tailwinds.append(f"Benign inflation ({inflation:.1f}%) supports growth")

        # Default sector-specific tailwinds/headwinds
        if sector in ("Technology", "Healthcare"):
            tailwinds.append("India as global services hub — structural tailwind")
        if sector == "Financial Services":
            tailwinds.append("India credit growth cycle — banking sector expansion")
        if sector == "Industrials":
            tailwinds.append("Government infrastructure capex push")

        macro_score = average_non_none(factor_scores) if factor_scores else 50.0

        if macro_score >= 65:
            assessment = "FAVORABLE"
        elif macro_score >= 45:
            assessment = "NEUTRAL"
        else:
            assessment = "CHALLENGING"

        return {
            "sector": sector,
            "macro_score": round(macro_score, 1),
            "tailwinds": tailwinds,
            "headwinds": headwinds,
            "assessment": assessment,
        }
