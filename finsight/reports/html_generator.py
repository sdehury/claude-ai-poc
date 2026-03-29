import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from finsight.models.report import AdvisoryReport
from finsight.models.mutual_fund import MFAnalysisResult
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = "./reports_output"


class HTMLReportGenerator:
    """Generate HTML reports from analysis results."""

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html"]),
        )

    def generate_stock_report(self, report: AdvisoryReport) -> str:
        """Generate an HTML stock analysis report. Returns the file path."""
        template = self.env.get_template("stock_report.html")
        html = template.render(
            report=report,
            fs=report.fundamental_score,
            ts=report.technical_signals,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        filename = f"{report.ticker}_analysis_{datetime.now():%Y%m%d}.html"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Stock report saved: {filepath}")
        return filepath

    def generate_mf_report(self, result: MFAnalysisResult) -> str:
        """Generate an HTML mutual fund report. Returns the file path."""
        template = self.env.get_template("mf_report.html")
        html = template.render(
            result=result,
            returns=result.returns,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        filename = f"MF_{result.scheme_code}_analysis_{datetime.now():%Y%m%d}.html"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"MF report saved: {filepath}")
        return filepath
