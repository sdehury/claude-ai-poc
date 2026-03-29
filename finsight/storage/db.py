import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(String, primary_key=True)  # symbol_date
    symbol = Column(String, nullable=False, index=True)
    asset_type = Column(String, nullable=False)
    analysis_date = Column(DateTime, default=datetime.now)
    fundamental_score = Column(Float)
    technical_trend = Column(String)
    overall_score = Column(Float)
    recommendation = Column(String)
    report_json = Column(Text)

    @classmethod
    def from_report(cls, report) -> "AnalysisRecord":
        date_str = datetime.now().strftime("%Y%m%d")
        return cls(
            id=f"{report.ticker}_{date_str}",
            symbol=report.ticker,
            asset_type=report.asset_type,
            fundamental_score=report.fundamental_score.overall_score if report.fundamental_score else None,
            technical_trend=report.technical_signals.trend if report.technical_signals else None,
            overall_score=report.overall_score,
            recommendation=report.recommendation,
            report_json=report.model_dump_json(),
        )


class PriceCache(Base):
    __tablename__ = "price_cache"

    key = Column(String, primary_key=True)
    data = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)


class Database:
    """SQLAlchemy database manager."""

    def __init__(self, db_url: str = "sqlite:///./data/finsight.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_report(self, report) -> None:
        session = self.Session()
        try:
            record = AnalysisRecord.from_report(report)
            session.merge(record)  # Upsert
            session.commit()
        finally:
            session.close()

    def get_report(self, symbol: str) -> dict | None:
        session = self.Session()
        try:
            record = (
                session.query(AnalysisRecord)
                .filter_by(symbol=symbol.upper())
                .order_by(AnalysisRecord.analysis_date.desc())
                .first()
            )
            if record and record.report_json:
                return json.loads(record.report_json)
            return None
        finally:
            session.close()

    def list_analyses(self, limit: int = 20) -> list[dict]:
        session = self.Session()
        try:
            records = (
                session.query(AnalysisRecord)
                .order_by(AnalysisRecord.analysis_date.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "symbol": r.symbol,
                    "asset_type": r.asset_type,
                    "date": r.analysis_date.isoformat() if r.analysis_date else None,
                    "score": r.overall_score,
                    "recommendation": r.recommendation,
                }
                for r in records
            ]
        finally:
            session.close()
