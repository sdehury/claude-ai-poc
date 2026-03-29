import os
from finsight.models.report import AdvisoryReport
from finsight.models.mutual_fund import MFAnalysisResult
from finsight.reports.html_generator import HTMLReportGenerator
from finsight.utils.logger import get_logger

logger = get_logger(__name__)


class PDFReportGenerator:
    """Generate PDF reports by converting HTML via WeasyPrint."""

    def __init__(self, output_dir: str = "./reports_output"):
        self.output_dir = output_dir
        self.html_generator = HTMLReportGenerator(output_dir)
        os.makedirs(output_dir, exist_ok=True)

    def generate_stock_report(self, report: AdvisoryReport) -> str:
        """Generate a PDF stock report. Returns the file path."""
        html_path = self.html_generator.generate_stock_report(report)
        pdf_path = html_path.replace(".html", ".pdf")

        try:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(pdf_path)
            logger.info(f"PDF report saved: {pdf_path}")
            return pdf_path
        except ImportError:
            logger.warning(
                "WeasyPrint not installed. Install with: pip install weasyprint. "
                "Returning HTML report instead."
            )
            return html_path

    def generate_mf_report(self, result: MFAnalysisResult) -> str:
        """Generate a PDF MF report. Returns the file path."""
        html_path = self.html_generator.generate_mf_report(result)
        pdf_path = html_path.replace(".html", ".pdf")

        try:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(pdf_path)
            logger.info(f"PDF report saved: {pdf_path}")
            return pdf_path
        except ImportError:
            logger.warning(
                "WeasyPrint not installed. Returning HTML report instead."
            )
            return html_path
